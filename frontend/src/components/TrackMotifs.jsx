import React from 'react';
import { normalizeTrack, getTrackConfig } from '../constants.js';

/**
 * Hand-drawn wobbly stroke SVG motifs and diagrams for each engineering track.
 * Tactile, imperfect, technical, not generic enterprise architecture drawings.
 */

export function TrackMotif({ trackName, className = 'track-motif-svg' }) {
  const track = normalizeTrack(trackName);
  const config = getTrackConfig(track);
  const color = config.color;

  switch (track) {
    case 'Operating Systems':
      // Concentric Privilege Rings (Ring 3 User -> Ring 1 -> Ring 0 Kernel)
      return (
        <svg viewBox="0 0 160 160" className={className} aria-hidden="true">
          {/* Ring 3 Outer */}
          <circle
            cx="80"
            cy="80"
            r="70"
            fill="none"
            stroke={color}
            strokeWidth="2.5"
            strokeDasharray="6 3"
            opacity="0.4"
          />
          {/* Ring 1/2 Drivers */}
          <circle
            cx="80"
            cy="80"
            r="48"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeDasharray="4 2"
            opacity="0.7"
          />
          {/* Ring 0 Kernel Core */}
          <circle cx="80" cy="80" r="26" fill={color} opacity="0.2" />
          <circle cx="80" cy="80" r="26" fill="none" stroke={color} strokeWidth="3.5" />
          {/* Trap / Syscall Trajectory */}
          <path
            d="M 30 80 Q 55 60 76 76"
            fill="none"
            stroke={color}
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          <polygon points="76,73 80,78 74,80" fill={color} />
          {/* Labels */}
          <text x="80" y="85" textAnchor="middle" fill={color} fontSize="12" fontWeight="700" fontFamily="Space Grotesk">
            RING 0
          </text>
          <text x="80" y="24" textAnchor="middle" fill="#807E78" fontSize="10" fontWeight="600" fontFamily="JetBrains Mono">
            RING 3 (USER)
          </text>
        </svg>
      );

    case 'Distributed Systems':
      // Distributed Consensus Quorum Nodes with packet arcs
      return (
        <svg viewBox="0 0 160 160" className={className} aria-hidden="true">
          {/* Connecting Mesh lines */}
          <path d="M 80 30 L 30 75 L 50 130 L 110 130 L 130 75 Z" fill="none" stroke={color} strokeWidth="1.5" strokeDasharray="3 3" opacity="0.4" />
          <path d="M 80 30 L 50 130" fill="none" stroke={color} strokeWidth="2" opacity="0.5" />
          <path d="M 80 30 L 110 130" fill="none" stroke={color} strokeWidth="2" opacity="0.5" />
          {/* Leader Node */}
          <circle cx="80" cy="30" r="16" fill={color} />
          <text x="80" y="34" textAnchor="middle" fill="#161514" fontSize="10" fontWeight="700" fontFamily="JetBrains Mono">L</text>
          {/* Follower Nodes */}
          <circle cx="30" cy="75" r="13" fill="#201F1D" stroke={color} strokeWidth="2.5" />
          <circle cx="130" cy="75" r="13" fill="#201F1D" stroke={color} strokeWidth="2.5" />
          <circle cx="50" cy="130" r="13" fill="#201F1D" stroke={color} strokeWidth="2.5" />
          <circle cx="110" cy="130" r="13" fill="#201F1D" stroke={color} strokeWidth="2.5" />
          <text x="80" y="90" textAnchor="middle" fill={color} fontSize="11" fontWeight="700" fontFamily="Space Grotesk">
            QUORUM 3/5
          </text>
        </svg>
      );

    case 'Databases & Storage':
      // B-Tree and LSM Append Log blocks
      return (
        <svg viewBox="0 0 160 160" className={className} aria-hidden="true">
          {/* Root page */}
          <rect x="45" y="25" width="70" height="26" rx="4" fill="#201F1D" stroke={color} strokeWidth="2.5" />
          <line x1="80" y1="25" x2="80" y2="51" stroke={color} strokeWidth="1.5" />
          <text x="80" y="42" textAnchor="middle" fill={color} fontSize="11" fontWeight="700" fontFamily="JetBrains Mono">[K1 | K2]</text>
          {/* Branching pointers */}
          <path d="M 60 51 L 35 85" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" />
          <path d="M 100 51 L 125 85" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" />
          {/* Leaf pages */}
          <rect x="15" y="85" width="55" height="24" rx="4" fill="#201F1D" stroke={color} strokeWidth="2" />
          <rect x="90" y="85" width="55" height="24" rx="4" fill="#201F1D" stroke={color} strokeWidth="2" />
          {/* Sequential WAL line */}
          <rect x="25" y="125" width="110" height="18" rx="2" fill={color} opacity="0.15" />
          <rect x="25" y="125" width="110" height="18" rx="2" fill="none" stroke={color} strokeWidth="2" strokeDasharray="5 3" />
          <text x="80" y="138" textAnchor="middle" fill={color} fontSize="9" fontWeight="700" fontFamily="JetBrains Mono">
            WAL APPEND LOG
          </text>
        </svg>
      );

    case 'Computer Networks':
      // TCP Three-Way Handshake SYN / ACK packet sequence
      return (
        <svg viewBox="0 0 160 160" className={className} aria-hidden="true">
          {/* Host Timelines */}
          <line x1="35" y1="20" x2="35" y2="140" stroke="#807E78" strokeWidth="2" strokeDasharray="3 3" />
          <line x1="125" y1="20" x2="125" y2="140" stroke="#807E78" strokeWidth="2" strokeDasharray="3 3" />
          <text x="35" y="15" textAnchor="middle" fill="#F5F2EB" fontSize="10" fontWeight="700" fontFamily="Space Grotesk">CLIENT</text>
          <text x="125" y="15" textAnchor="middle" fill="#F5F2EB" fontSize="10" fontWeight="700" fontFamily="Space Grotesk">SERVER</text>
          {/* Packet 1: SYN */}
          <path d="M 35 40 L 120 65" fill="none" stroke={color} strokeWidth="2.5" />
          <polygon points="120,60 125,65 118,68" fill={color} />
          <text x="75" y="48" textAnchor="middle" fill={color} fontSize="10" fontWeight="700" fontFamily="JetBrains Mono">SYN</text>
          {/* Packet 2: SYN-ACK */}
          <path d="M 125 75 L 40 100" fill="none" stroke={color} strokeWidth="2.5" />
          <polygon points="42,95 35,100 44,103" fill={color} />
          <text x="85" y="84" textAnchor="middle" fill={color} fontSize="10" fontWeight="700" fontFamily="JetBrains Mono">SYN-ACK</text>
          {/* Packet 3: ACK */}
          <path d="M 35 110 L 120 130" fill="none" stroke={color} strokeWidth="2.5" />
          <polygon points="120,125 125,130 118,133" fill={color} />
          <text x="75" y="118" textAnchor="middle" fill={color} fontSize="10" fontWeight="700" fontFamily="JetBrains Mono">ACK</text>
        </svg>
      );

    case 'DSA':
      // Binary Tree Traversal with Balancer
      return (
        <svg viewBox="0 0 160 160" className={className} aria-hidden="true">
          {/* Traversal branches */}
          <path d="M 80 35 L 45 75" fill="none" stroke={color} strokeWidth="2.5" />
          <path d="M 80 35 L 115 75" fill="none" stroke={color} strokeWidth="2.5" />
          <path d="M 45 75 L 25 115" fill="none" stroke={color} strokeWidth="2" strokeDasharray="3 2" />
          <path d="M 45 75 L 65 115" fill="none" stroke={color} strokeWidth="2" strokeDasharray="3 2" />
          {/* Root node */}
          <circle cx="80" cy="35" r="16" fill={color} />
          <text x="80" y="40" textAnchor="middle" fill="#161514" fontSize="12" fontWeight="700" fontFamily="JetBrains Mono">50</text>
          {/* Child nodes */}
          <circle cx="45" cy="75" r="14" fill="#201F1D" stroke={color} strokeWidth="2.5" />
          <text x="45" y="80" textAnchor="middle" fill={color} fontSize="11" fontWeight="700" fontFamily="JetBrains Mono">25</text>
          <circle cx="115" cy="75" r="14" fill="#201F1D" stroke={color} strokeWidth="2.5" />
          <text x="115" y="80" textAnchor="middle" fill={color} fontSize="11" fontWeight="700" fontFamily="JetBrains Mono">75</text>
          {/* Leaf nodes */}
          <circle cx="25" cy="115" r="11" fill="#201F1D" stroke={color} strokeWidth="2" />
          <circle cx="65" cy="115" r="11" fill="#201F1D" stroke={color} strokeWidth="2" />
          <text x="80" y="145" textAnchor="middle" fill={color} fontSize="10" fontWeight="700" fontFamily="Space Grotesk">O(log N) SEARCH</text>
        </svg>
      );

    case 'AI & Machine Learning':
      // Multi-layer Neural Weights
      return (
        <svg viewBox="0 0 160 160" className={className} aria-hidden="true">
          {/* Synapse connections */}
          <line x1="35" y1="45" x2="80" y2="35" stroke={color} strokeWidth="1.5" opacity="0.4" />
          <line x1="35" y1="45" x2="80" y2="80" stroke={color} strokeWidth="2" opacity="0.6" />
          <line x1="35" y1="115" x2="80" y2="80" stroke={color} strokeWidth="2" opacity="0.6" />
          <line x1="35" y1="115" x2="80" y2="125" stroke={color} strokeWidth="1.5" opacity="0.4" />
          <line x1="80" y1="35" x2="125" y2="80" stroke={color} strokeWidth="2.5" />
          <line x1="80" y1="80" x2="125" y2="80" stroke={color} strokeWidth="2.5" />
          <line x1="80" y1="125" x2="125" y2="80" stroke={color} strokeWidth="2.5" />
          {/* Input Layer */}
          <circle cx="35" cy="45" r="12" fill="#201F1D" stroke={color} strokeWidth="2.5" />
          <circle cx="35" cy="115" r="12" fill="#201F1D" stroke={color} strokeWidth="2.5" />
          {/* Hidden Layer */}
          <circle cx="80" cy="35" r="12" fill="#201F1D" stroke={color} strokeWidth="2.5" />
          <circle cx="80" cy="80" r="13" fill={color} opacity="0.3" />
          <circle cx="80" cy="80" r="13" fill="none" stroke={color} strokeWidth="3" />
          <circle cx="80" cy="125" r="12" fill="#201F1D" stroke={color} strokeWidth="2.5" />
          {/* Output Node */}
          <circle cx="125" cy="80" r="14" fill={color} />
          <text x="125" y="85" textAnchor="middle" fill="#161514" fontSize="10" fontWeight="700" fontFamily="JetBrains Mono">ŷ</text>
        </svg>
      );

    case 'System Design':
      // Client -> Load Balancer -> Horizontal Worker Nodes
      return (
        <svg viewBox="0 0 160 160" className={className} aria-hidden="true">
          {/* Client */}
          <rect x="15" y="65" width="30" height="30" rx="4" fill="#201F1D" stroke={color} strokeWidth="2.5" />
          <text x="30" y="83" textAnchor="middle" fill={color} fontSize="9" fontWeight="700" fontFamily="JetBrains Mono">APP</text>
          {/* Fanout to LB */}
          <line x1="45" y1="80" x2="68" y2="80" stroke={color} strokeWidth="2" />
          {/* Load Balancer */}
          <polygon points="68,60 84,60 88,100 64,100" fill={color} opacity="0.2" />
          <polygon points="68,60 84,60 88,100 64,100" fill="none" stroke={color} strokeWidth="2.5" />
          <text x="76" y="84" textAnchor="middle" fill={color} fontSize="9" fontWeight="700" fontFamily="JetBrains Mono">LB</text>
          {/* Worker fanout */}
          <path d="M 88 70 L 115 45" fill="none" stroke={color} strokeWidth="2" />
          <path d="M 88 80 L 115 80" fill="none" stroke={color} strokeWidth="2" />
          <path d="M 88 90 L 115 115" fill="none" stroke={color} strokeWidth="2" />
          {/* Replicas */}
          <rect x="115" y="32" width="32" height="22" rx="3" fill="#201F1D" stroke={color} strokeWidth="2" />
          <rect x="115" y="69" width="32" height="22" rx="3" fill="#201F1D" stroke={color} strokeWidth="2" />
          <rect x="115" y="106" width="32" height="22" rx="3" fill="#201F1D" stroke={color} strokeWidth="2" />
          <text x="80" y="145" textAnchor="middle" fill={color} fontSize="10" fontWeight="700" fontFamily="Space Grotesk">N-TIER SCALE</text>
        </svg>
      );

    case 'Developer Tools':
      // Git DAG commit tree
      return (
        <svg viewBox="0 0 160 160" className={className} aria-hidden="true">
          {/* Main branch line */}
          <line x1="30" y1="100" x2="135" y2="100" stroke={color} strokeWidth="3" />
          {/* Feature branch line */}
          <path d="M 60 100 C 70 60, 80 60, 95 60 L 110 60 C 120 60, 125 75, 130 95" fill="none" stroke={color} strokeWidth="2.5" strokeDasharray="4 2" />
          {/* Commits on main */}
          <circle cx="35" cy="100" r="8" fill={color} />
          <circle cx="60" cy="100" r="8" fill={color} />
          <circle cx="95" cy="100" r="8" fill={color} />
          <circle cx="130" cy="100" r="9" fill={color} />
          {/* Commit on feature branch */}
          <circle cx="95" cy="60" r="8" fill="#201F1D" stroke={color} strokeWidth="3" />
          {/* Tag */}
          <text x="130" y="125" textAnchor="middle" fill={color} fontSize="10" fontWeight="700" fontFamily="JetBrains Mono">HEAD</text>
          <text x="80" y="35" textAnchor="middle" fill="#807E78" fontSize="10" fontWeight="700" fontFamily="Space Grotesk">MERGE COMMIT</text>
        </svg>
      );

    default:
      // Weekly Puzzle / Technical Mystery
      return (
        <svg viewBox="0 0 160 160" className={className} aria-hidden="true">
          {/* Logic Gates XOR & Interlocking blocks */}
          <rect x="35" y="35" width="42" height="42" rx="4" fill="#201F1D" stroke={color} strokeWidth="3" />
          <rect x="75" y="35" width="42" height="42" rx="4" fill={color} opacity="0.3" stroke={color} strokeWidth="3" />
          <rect x="35" y="75" width="42" height="42" rx="4" fill={color} opacity="0.3" stroke={color} strokeWidth="3" />
          <rect x="75" y="75" width="42" height="42" rx="4" fill="#201F1D" stroke={color} strokeWidth="3" />
          <text x="56" y="62" textAnchor="middle" fill={color} fontSize="16" fontWeight="700" fontFamily="JetBrains Mono">1</text>
          <text x="96" y="62" textAnchor="middle" fill="#161514" fontSize="16" fontWeight="700" fontFamily="JetBrains Mono">0</text>
          <text x="56" y="102" textAnchor="middle" fill="#161514" fontSize="16" fontWeight="700" fontFamily="JetBrains Mono">0</text>
          <text x="96" y="102" textAnchor="middle" fill={color} fontSize="16" fontWeight="700" fontFamily="JetBrains Mono">1</text>
          <text x="80" y="138" textAnchor="middle" fill={color} fontSize="11" fontWeight="700" fontFamily="Space Grotesk">BIT XOR ^</text>
        </svg>
      );
  }
}
