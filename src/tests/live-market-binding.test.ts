import { describe, expect, it } from 'vitest';
import { toHomeCardData } from '../lib/live-data';

describe('live market binding', () => {
  it('maps summary response without changing screen structure assumptions', () => {
    const result = toHomeCardData({
      marketMood: '중립',
      fearGreedIndex: 50,
      advancers: 5,
      decliners: 4,
      sentimentMix: { positive: 55, negative: 45 },
      aiSummary: '중립 구간',
    });

    expect(result.fearGreed).toBe(50);
    expect(result.aiSummary).toContain('중립');
  });
});
