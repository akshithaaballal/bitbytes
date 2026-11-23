import assert from 'node:assert';
import {
  extractCoreExplanation,
  getPostHook,
  renderInlineMarkdown,
  buildPostSlides
} from '../src/utils/slideParser.js';

console.log('Testing slideParser.js utilities...');

// 1. Test extractCoreExplanation
{
  const text1 = "As you might have heard recently, Cloudflare had an issue. So what is Raft Consensus? Let's learn about this: Raft guarantees state machine replication across a cluster.";
  const extracted1 = extractCoreExplanation(text1);
  assert.ok(extracted1.length > 20, 'Should extract core explanation');
  assert.ok(!extracted1.toLowerCase().startsWith('as you might have heard'), 'Should strip synthetic news prefix');
  assert.ok(extracted1.startsWith('R') || extracted1.startsWith('W') || extracted1.startsWith('L'), 'Should be capitalized');

  const plainText = "Virtual memory allows applications to address more memory than physically installed.";
  const extracted2 = extractCoreExplanation(plainText);
  assert.strictEqual(extracted2, plainText, 'Plain text without lead-in should remain intact');

  console.log('✅ extractCoreExplanation passed');
}

// 2. Test getPostHook
{
  const post1 = {
    title: 'Kernel Space vs. User Space Protection Rings',
    track: 'Operating Systems'
  };
  const hook1 = getPostHook(post1);
  assert.strictEqual(hook1, "Why doesn't one crashing app freeze your entire laptop?", 'Curated hook should match');

  const post2 = {
    title: 'Unheard Of Algorithm In Rust',
    track: 'Operating Systems'
  };
  const hook2 = getPostHook(post2);
  assert.ok(hook2.includes('Unheard Of Algorithm In Rust'), 'Fallback hook should generate natural question');

  console.log('✅ getPostHook passed');
}

// 3. Test renderInlineMarkdown
{
  const renderedEmpty = renderInlineMarkdown('');
  assert.strictEqual(renderedEmpty, '', 'Empty string returns empty');

  const renderedTokens = renderInlineMarkdown('Check `malloc()` and **free()** calls');
  assert.strictEqual(renderedTokens.length, 5, 'Should segment into text, code, and bold elements');
  assert.strictEqual(renderedTokens[1].type, 'code', 'Code element type matches');
  assert.strictEqual(renderedTokens[3].type, 'strong', 'Bold element type matches');

  console.log('✅ renderInlineMarkdown passed');
}

// 4. Test buildPostSlides
{
  const samplePost = {
    id: 'test_post_01',
    title: 'Distributed Two-Phase Locking',
    track: 'Distributed Systems',
    subtitle: 'Concurrency Control in Sharded Stores',
    summary: 'Two-phase locking prevents data races across partitioned tables.',
    key_points: [
      'Growing phase acquires locks without releasing any',
      'Shrinking phase releases locks without acquiring any',
      'Avoids cascading aborts under strict 2PL'
    ],
    code_snippet: 'class LockManager:\n    def acquire(self, lock):\n        pass',
    interview_tip: 'Mention deadlocks and wound-wait detection.'
  };

  const slides = buildPostSlides(samplePost);
  assert.ok(slides.length >= 4, 'Should generate at least 4 slides');
  assert.strictEqual(slides[0].type, 'hook', 'First slide is hook');
  assert.strictEqual(slides[1].type, 'mental_model', 'Second slide is mental model explanation');
  assert.ok(slides.some(s => s.type === 'code'), 'Includes code slide');
  assert.ok(slides.some(s => s.type === 'complexity'), 'Includes complexity slide');
  assert.ok(slides.some(s => s.type === 'source'), 'Includes source slide');

  console.log('✅ buildPostSlides passed');
}

console.log('\nAll slideParser unit test cases passed successfully!');
