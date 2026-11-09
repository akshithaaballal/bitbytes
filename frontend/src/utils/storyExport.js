import { getTrackConfig, normalizeTrack } from '../constants.js';
import { getPostHook, extractCoreExplanation } from './slideParser.js';

/**
 * Renders a crisp 1080x1920 vertical 9:16 story card onto an offscreen canvas
 * and downloads it as a PNG with the BitBytes watermark in the corner.
 */
export async function exportSlideAsStory(post, slideIndex = 0) {
  const canvas = document.createElement('canvas');
  canvas.width = 1080;
  canvas.height = 1920;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const trackName = normalizeTrack(post.track);
  const track = getTrackConfig(trackName);
  const hook = getPostHook(post);
  const coreText = extractCoreExplanation(post.summary);

  // 1. Dark warm charcoal background (neo-brutalist poster aesthetic)
  ctx.fillStyle = '#161514';
  ctx.fillRect(0, 0, 1080, 1920);

  // 2. Track color header band
  ctx.fillStyle = track.color;
  ctx.fillRect(0, 0, 1080, 24);

  // 3. Top Watermark Header
  ctx.fillStyle = '#F5F2EB';
  ctx.font = '700 42px "Space Grotesk", sans-serif';
  ctx.fillText('⚡ BITBYTES', 80, 130);

  ctx.fillStyle = track.color;
  ctx.font = '700 28px "Space Grotesk", sans-serif';
  ctx.fillText(`@csbites • ${track.shortLabel.toUpperCase()}`, 80, 180);

  ctx.fillStyle = '#807E78';
  ctx.font = '500 24px "JetBrains Mono", monospace';
  ctx.fillText(`BITE #${(post.id || 'NOTE').slice(-12)}`, 740, 130);

  // 4. Poster Card Box
  const cardX = 80;
  const cardY = 240;
  const cardW = 920;
  const cardH = 1420;

  // Solid offset shadow
  ctx.fillStyle = track.color;
  ctx.fillRect(cardX + 16, cardY + 16, cardW, cardH);

  // Main Card
  ctx.fillStyle = '#201F1D';
  ctx.fillRect(cardX, cardY, cardW, cardH);

  ctx.strokeStyle = '#F5F2EB';
  ctx.lineWidth = 6;
  ctx.strokeRect(cardX, cardY, cardW, cardH);

  // Track accent line inside card
  ctx.fillStyle = track.color;
  ctx.fillRect(cardX, cardY, cardW, 16);

  // Track Pill
  ctx.fillStyle = track.color;
  ctx.fillRect(cardX + 60, cardY + 70, 220, 50);

  ctx.fillStyle = '#161514';
  ctx.font = '700 24px "Space Grotesk", sans-serif';
  ctx.fillText(track.shortLabel.toUpperCase(), cardX + 80, cardY + 104);

  // Title / Topic
  ctx.fillStyle = '#F5F2EB';
  ctx.font = '700 58px "Space Grotesk", sans-serif';
  wrapText(ctx, post.title, cardX + 60, cardY + 220, cardW - 120, 72, 3);

  // Divider Line
  ctx.strokeStyle = '#363430';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(cardX + 60, cardY + 480);
  ctx.lineTo(cardX + cardW - 60, cardY + 480);
  ctx.stroke();

  // Hook Scenario Box
  ctx.fillStyle = '#2A2926';
  ctx.fillRect(cardX + 60, cardY + 530, cardW - 120, 220);
  ctx.strokeStyle = track.color;
  ctx.lineWidth = 3;
  ctx.strokeRect(cardX + 60, cardY + 530, cardW - 120, 220);

  ctx.fillStyle = track.color;
  ctx.font = '700 24px "Space Grotesk", sans-serif';
  ctx.fillText('THE HOOK', cardX + 90, cardY + 580);

  ctx.fillStyle = '#F5F2EB';
  ctx.font = '500 36px "Space Grotesk", sans-serif';
  wrapText(ctx, `"${hook}"`, cardX + 90, cardY + 630, cardW - 180, 48, 2);

  // Core Concept Body
  ctx.fillStyle = '#B0ADA6';
  ctx.font = '400 32px "IBM Plex Sans", sans-serif';
  wrapText(ctx, coreText, cardX + 60, cardY + 840, cardW - 120, 46, 5);

  // Code or Complexity Snippet Preview
  if (post.code_snippet) {
    const codeSnippet = post.code_snippet.split('\n').slice(0, 4).join('\n');
    ctx.fillStyle = '#161514';
    ctx.fillRect(cardX + 60, cardY + 1120, cardW - 120, 230);
    ctx.strokeStyle = '#363430';
    ctx.lineWidth = 2;
    ctx.strokeRect(cardX + 60, cardY + 1120, cardW - 120, 230);

    ctx.fillStyle = track.color;
    ctx.font = '500 20px "JetBrains Mono", monospace';
    ctx.fillText('// CODE SNIPPET', cardX + 90, cardY + 1160);

    ctx.fillStyle = '#CCFF00';
    ctx.font = '400 24px "JetBrains Mono", monospace';
    const lines = codeSnippet.split('\n');
    lines.forEach((line, idx) => {
      ctx.fillText(line.slice(0, 52), cardX + 90, cardY + 1210 + idx * 36);
    });
  }

  // 5. Watermark Footer
  ctx.fillStyle = '#F5F2EB';
  ctx.font = '700 34px "Space Grotesk", sans-serif';
  ctx.fillText('Follow @csbites on Telegram', 80, 1760);

  ctx.fillStyle = '#807E78';
  ctx.font = '400 26px "IBM Plex Sans", sans-serif';
  ctx.fillText('Bite-sized systems engineering notes dropped twice daily', 80, 1805);

  // Export blob and trigger download
  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        resolve(false);
        return;
      }
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `bitbytes_${post.id || 'bite'}_story.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => URL.revokeObjectURL(url), 5000);
      resolve(true);
    }, 'image/png');
  });
}

function wrapText(ctx, text, x, y, maxWidth, lineHeight, maxLines = 4) {
  if (!text) return;
  const words = text.split(' ');
  let line = '';
  let linesRendered = 0;

  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + ' ';
    const metrics = ctx.measureText(testLine);
    if (metrics.width > maxWidth && n > 0) {
      if (linesRendered >= maxLines - 1) {
        ctx.fillText(line.trim() + '...', x, y);
        return;
      }
      ctx.fillText(line.trim(), x, y);
      line = words[n] + ' ';
      y += lineHeight;
      linesRendered++;
    } else {
      line = testLine;
    }
  }
  if (linesRendered < maxLines) {
    ctx.fillText(line.trim(), x, y);
  }
}
