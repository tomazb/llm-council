import React, { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage3.css';

const Stage3 = memo(function Stage3({ finalResponse }) {
  if (!finalResponse) {
    return (
      <div className="stage3">
        <h3>Stage 3: Final Synthesis</h3>
        <p>No final response available</p>
      </div>
    );
  }

  return (
    <div className="stage3">
      <h3>Stage 3: Final Synthesis</h3>
      <div className="final-response">
        <div className="response-header">
          <h4>{finalResponse.model}</h4>
        </div>
        <div className="response-content">
          <ReactMarkdown>{finalResponse.response}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
});

export default Stage3;
