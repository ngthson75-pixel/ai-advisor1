import { describe, it, expect } from 'vitest'

describe('App Tests', () => {
  it('should pass basic test', () => {
    expect(true).toBe(true)
  })
  
  it('should do math correctly', () => {
    expect(2 + 2).toBe(4)
  })
})
