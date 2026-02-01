/**
 * SignalsModule Component Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import SignalsModule from '../components/SignalsModule'

describe('SignalsModule', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Initial Render', () => {
    it('renders without crashing', () => {
      render(<SignalsModule />)
      expect(screen.getByText(/tín hiệu/i)).toBeInTheDocument()
    })

    it('shows loading state initially', () => {
      render(<SignalsModule />)
      expect(screen.getByText(/đang tải/i)).toBeInTheDocument()
    })
  })

  describe('Data Loading', () => {
    it('loads and displays signals successfully', async () => {
      // Mock successful API response
      global.mockFetchSuccess({
        success: true,
        signals: [
          {
            id: 1,
            ticker: 'VCB',
            strategy: 'PULLBACK',
            entry_price: 88500,
            action: 'BUY',
            strength: 75,
            date: '2026-01-31'
          }
        ]
      })

      render(<SignalsModule />)

      // Should show loading first
      expect(screen.getByText(/đang tải/i)).toBeInTheDocument()

      // Wait for signals to load
      await waitFor(() => {
        expect(screen.getByText('VCB')).toBeInTheDocument()
      })

      // Check signal details
      expect(screen.getByText('88,500')).toBeInTheDocument()
      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('shows empty state when no signals', async () => {
      global.mockFetchSuccess({
        success: true,
        signals: []
      })

      render(<SignalsModule />)

      await waitFor(() => {
        expect(screen.getByText(/chưa có tín hiệu/i)).toBeInTheDocument()
      })
    })

    it('handles API errors gracefully', async () => {
      global.mockFetchError(500, 'Server error')

      render(<SignalsModule />)

      await waitFor(() => {
        expect(screen.getByText(/lỗi/i)).toBeInTheDocument()
      })
    })
  })

  describe('User Interactions', () => {
    it('refreshes signals when refresh button clicked', async () => {
      global.mockFetchSuccess({
        success: true,
        signals: []
      })

      render(<SignalsModule />)

      await waitFor(() => {
        expect(screen.queryByText(/đang tải/i)).not.toBeInTheDocument()
      })

      // Mock another successful response
      global.mockFetchSuccess({
        success: true,
        signals: [
          { id: 1, ticker: 'VCB', action: 'BUY', strength: 75 }
        ]
      })

      // Click refresh button
      const refreshBtn = screen.getByText(/làm mới|refresh/i)
      fireEvent.click(refreshBtn)

      // Should show loading again
      expect(screen.getByText(/đang tải/i)).toBeInTheDocument()
    })

    it('filters BUY signals correctly', async () => {
      global.mockFetchSuccess({
        success: true,
        signals: [
          { id: 1, ticker: 'VCB', action: 'BUY', strength: 75 },
          { id: 2, ticker: 'VHM', action: 'SELL', strength: 80 }
        ]
      })

      render(<SignalsModule />)

      await waitFor(() => {
        expect(screen.getByText('VCB')).toBeInTheDocument()
      })

      // Click BUY tab
      const buyTab = screen.getByText(/mua/i)
      fireEvent.click(buyTab)

      // Should show only BUY signals
      expect(screen.getByText('VCB')).toBeInTheDocument()
      expect(screen.queryByText('VHM')).not.toBeInTheDocument()
    })
  })

  describe('API Integration', () => {
    it('calls correct API endpoint', async () => {
      global.mockFetchSuccess({
        success: true,
        signals: []
      })

      render(<SignalsModule />)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/signals')
        )
      })
    })

    it('handles network errors', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'))

      render(<SignalsModule />)

      await waitFor(() => {
        expect(screen.getByText(/lỗi kết nối/i)).toBeInTheDocument()
      })
    })
  })

  describe('Data Validation', () => {
    it('validates signal data structure', async () => {
      const invalidSignal = {
        // Missing required fields
        id: 1
      }

      global.mockFetchSuccess({
        success: true,
        signals: [invalidSignal]
      })

      render(<SignalsModule />)

      // Component should handle invalid data gracefully
      await waitFor(() => {
        // Should not crash
        expect(screen.queryByText(/undefined/i)).not.toBeInTheDocument()
      })
    })
  })
})
