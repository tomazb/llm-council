import React, { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage2.css';

const Stage2 = memo(function Stage2({ rankings, labelToModel, aggregateRankings }) {
  if (!rankings || rankings.length === 0) {
    return (
      <div className="stage2">
        <h3>Stage 2: Peer Rankings</h3>
        <p>No rankings available</p>
      </div>
    );
  }

  return (
    <div className="stage2">
      <h3>Stage 2: Peer Rankings</h3>
      
      {/* Aggregate Rankings */}
      {aggregateRankings && aggregateRankings.length > 0 && (
        <div className="aggregate-rankings">
          <h4>Aggregate Rankings</h4>
          <div className="ranking-list">
            {aggregateRankings.map((item, index) => (
              <div key={item.model} className="ranking-item">
                <span className="rank">#{index + 1}</span>
                <span className="model-name">{item.model}</span>
                <span className="avg-rank">Avg: {item.average_rank}</span>
                <span className="rank-count">({item.rankings_count} votes)</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Individual Rankings */}
      <div className="individual-rankings">
        <h4>Individual Model Rankings</h4>
        <div className="rankings-grid">
          {rankings.map((ranking, index) => (
            <div key={index} className="ranking-card">
              <div className="ranking-header">
                <h5>{ranking.model}</h5>
              </div>
              <div className="ranking-content">
                <ReactMarkdown>{ranking.ranking}</ReactMarkdown>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

export default Stage2;
