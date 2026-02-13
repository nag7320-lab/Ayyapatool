"""Chat / RAG AI advisor endpoints with SSE streaming."""

import json
import logging

from flask import Blueprint, Response, jsonify, request, stream_with_context
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db, limiter
from app.models.rag import ChatMessage, ChatSession

chat_bp = Blueprint("chat", __name__)
logger = logging.getLogger(__name__)


@chat_bp.route("/message", methods=["POST"])
@jwt_required()
@limiter.limit("100/hour")
def chat_message():
    """
    SSE streaming RAG endpoint.

    Request:
    {
        "query": "What is GST rate on software services?",
        "category": "gst",  // Optional
        "session_id": "uuid"  // Optional
    }

    Response: Server-Sent Events
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query is required"}), 400

    if len(query) > 1000:
        return jsonify({"error": "Query too long (max 1000 characters)"}), 400

    category = data.get("category")
    session_id = data.get("session_id")

    # Get or create session
    if session_id:
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    else:
        session = ChatSession(user_id=user_id, title=query[:100])
        db.session.add(session)
        db.session.commit()

    if not session:
        return jsonify({"error": "Session not found"}), 404

    # Save user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=query)
    db.session.add(user_msg)
    db.session.commit()

    def generate():
        """Stream RAG pipeline response."""
        try:
            from flask import current_app
            from app.services.rag.pipeline import RAGPipeline

            config = current_app.config
            rag = RAGPipeline(config=config)

            full_answer = ""
            confidence = 0
            sources = []

            for sse_event in rag.process_query_stream(query, category, user_id):
                yield sse_event

                # Parse to collect full answer
                if sse_event.startswith("data: "):
                    try:
                        event_data = json.loads(sse_event[6:].strip())
                        if event_data.get("type") == "chunk":
                            full_answer += event_data.get("content", "")
                        elif event_data.get("type") == "done":
                            confidence = event_data.get("confidence", 0)
                            sources = event_data.get("sources", [])
                    except json.JSONDecodeError:
                        pass

            # Save assistant message
            assistant_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=full_answer,
                intent_category=category,
                confidence=confidence,
                sources=sources,
            )
            db.session.add(assistant_msg)
            db.session.commit()

        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': 'An error occurred'})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@chat_bp.route("/sessions", methods=["GET"])
@jwt_required()
def list_sessions():
    """List user's chat sessions."""
    user_id = get_jwt_identity()
    sessions = (
        ChatSession.query.filter_by(user_id=user_id, is_active=True)
        .order_by(ChatSession.updated_at.desc())
        .limit(50)
        .all()
    )

    return jsonify({
        "sessions": [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
            for s in sessions
        ]
    })


@chat_bp.route("/sessions/<session_id>/messages", methods=["GET"])
@jwt_required()
def get_session_messages(session_id):
    """Get all messages in a chat session."""
    user_id = get_jwt_identity()
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify({
        "session_id": session.id,
        "title": session.title,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "confidence": m.confidence,
                "sources": m.sources,
                "created_at": m.created_at.isoformat(),
            }
            for m in session.messages
        ],
    })
