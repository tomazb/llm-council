import React, { memo } from 'react';
import './Sidebar.css';

const Sidebar = memo(function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation
}) {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>LLM Council</h2>
        <button className="new-conversation-btn" onClick={onNewConversation}>
          + New Conversation
        </button>
      </div>
      
      <div className="conversations-list">
        {conversations.length === 0 ? (
          <div className="empty-conversations">
            <p>No conversations yet</p>
            <p>Create your first conversation to get started</p>
          </div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${
                conv.id === currentConversationId ? 'active' : ''
              }`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div className="conversation-title">{conv.title}</div>
              <div className="conversation-meta">
                <span className="message-count">{conv.message_count} messages</span>
                <span className="conversation-date">{formatDate(conv.created_at)}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
});

export default Sidebar;
