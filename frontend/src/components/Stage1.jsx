import React, { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage1.css';

const Stage1 = memo(function Stage1({ responses }) {
  if (!responses || responses.length === 0) {
    return (
      <div className="stage1">
        <h3>Stage 1: Individual Responses</h3>
        <p>No responses available</p>
      </div>
    );
  }

  return (
    <div className="stage1">
      <h3>Stage 1: Individual Responses</h3>
      <div className="responses-grid">
        {responses.map((response, index) => (
          <div key={index} className="response-card">
            <div className="response-header">
              <h4>{response.model}</h4>
            </div>
            <div className="response-content">
              <ReactMarkdown>{response.response}</ReactMarkdown>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
});

export default Stage1;
