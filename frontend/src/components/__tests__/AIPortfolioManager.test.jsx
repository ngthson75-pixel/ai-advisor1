/**
 * AIPortfolioManager Component Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import AIPortfolioManager from '../components/AIPortfolioManager'

describe('AIPortfolioManager', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Portfolio Display', () => {
    it('loads and displays portfolio', async () => {
      global.mockFetchSuccess({
        success: true,
        portfolio: [
          {
            ticker: 'VCB',
            quantity: 100,
            avg_price: 85000,
            current_price: 88500
          }
        ]
      })

      render(<AIPortfolioManager />)

      await waitFor(() => {
        expect(screen.getByText('VCB')).toBeInTheDocument()
        expect(screen.getByText('100')).toBeInTheDocument()
      })
    })

    it('shows empty portfolio message', async () => {
      global.mockFetchSuccess({
        success: true,
        portfolio: []
      })

      render(<AIPortfolioManager />)

      await waitFor(() => {
        expect(screen.getByText(/chưa có cổ phiếu/i)).toBeInTheDocument()
      })
    })

    it('calculates total value correctly', async () => {
      global.mockFetchSuccess({
        success: true,
        portfolio: [
          {
            ticker: 'VCB',
            quantity: 100,
            avg_price: 85000,
            current_price: 88500
          }
        ]
      })

      render(<AIPortfolioManager />)

      await waitFor(() => {
        // Total value = 100 * 88,500 = 8,850,000
        expect(screen.getByText(/8,850,000/)).toBeInTheDocument()
      })
    })
  })

  describe('Add Stock', () => {
    it('adds stock to portfolio successfully', async () => {
      // Mock initial empty portfolio
      global.mockFetchSuccess({
        success: true,
        portfolio: []
      })

      render(<AIPortfolioManager />)

      await waitFor(() => {
        expect(screen.getByText(/chưa có cổ phiếu/i)).toBeInTheDocument()
      })

      // Fill form
      const tickerInput = screen.getByPlaceholderText(/mã cổ phiếu/i)
      const quantityInput = screen.getByPlaceholderText(/số lượng/i)
      const priceInput = screen.getByPlaceholderText(/giá/i)

      fireEvent.change(tickerInput, { target: { value: 'VCB' } })
      fireEvent.change(quantityInput, { target: { value: '100' } })
      fireEvent.change(priceInput, { target: { value: '85000' } })

      // Mock add response
      global.mockFetchSuccess({
        success: true
      })

      // Click add button
      const addBtn = screen.getByText(/thêm/i)
      fireEvent.click(addBtn)

      // Should show success message
      await waitFor(() => {
        expect(screen.getByText(/thêm thành công/i)).toBeInTheDocument()
      })
    })

    it('validates stock ticker format', async () => {
      render(<AIPortfolioManager />)

      const tickerInput = screen.getByPlaceholderText(/mã cổ phiếu/i)
      
      // Invalid ticker (lowercase)
      fireEvent.change(tickerInput, { target: { value: 'vcb' } })
      
      const addBtn = screen.getByText(/thêm/i)
      fireEvent.click(addBtn)

      // Should show error
      await waitFor(() => {
        expect(screen.getByText(/mã không hợp lệ/i)).toBeInTheDocument()
      })
    })
  })

  describe('AI Chat Integration', () => {
    it('sends message to AI and displays response', async () => {
      render(<AIPortfolioManager />)

      const messageInput = screen.getByPlaceholderText(/hỏi ai/i)
      fireEvent.change(messageInput, { 
        target: { value: 'Tôi nên mua VCB không?' } 
      })

      // Mock AI response
      global.mockFetchSuccess({
        success: true,
        response: 'Dựa trên phân tích, VCB là cổ phiếu tốt...'
      })

      const sendBtn = screen.getByText(/gửi/i)
      fireEvent.click(sendBtn)

      await waitFor(() => {
        expect(screen.getByText(/VCB là cổ phiếu tốt/i)).toBeInTheDocument()
      })
    })

    it('includes portfolio context in AI chat', async () => {
      // Mock portfolio
      global.mockFetchSuccess({
        success: true,
        portfolio: [
          { ticker: 'VCB', quantity: 100 }
        ]
      })

      render(<AIPortfolioManager />)

      await waitFor(() => {
        expect(screen.getByText('VCB')).toBeInTheDocument()
      })

      const messageInput = screen.getByPlaceholderText(/hỏi ai/i)
      fireEvent.change(messageInput, { 
        target: { value: 'Phân tích danh mục của tôi' } 
      })

      global.mockFetchSuccess({
        success: true,
        response: 'Danh mục của bạn có VCB...'
      })

      const sendBtn = screen.getByText(/gửi/i)
      fireEvent.click(sendBtn)

      // Check API was called with portfolio context
      await waitFor(() => {
        const calls = global.fetch.mock.calls
        const chatCall = calls.find(call => 
          call[0].includes('/api/chat')
        )
        expect(chatCall).toBeDefined()
      })
    })
  })

  describe('Delete Stock', () => {
    it('removes stock from portfolio', async () => {
      // Mock portfolio with stock
      global.mockFetchSuccess({
        success: true,
        portfolio: [
          { ticker: 'VCB', quantity: 100 }
        ]
      })

      render(<AIPortfolioManager />)

      await waitFor(() => {
        expect(screen.getByText('VCB')).toBeInTheDocument()
      })

      // Mock delete response
      global.mockFetchSuccess({
        success: true
      })

      // Click delete button
      const deleteBtn = screen.getByText(/xóa/i)
      fireEvent.click(deleteBtn)

      // Should show confirmation
      await waitFor(() => {
        expect(screen.getByText(/xác nhận xóa/i)).toBeInTheDocument()
      })

      // Confirm deletion
      const confirmBtn = screen.getByText(/đồng ý/i)
      fireEvent.click(confirmBtn)

      // Stock should be removed
      await waitFor(() => {
        expect(screen.queryByText('VCB')).not.toBeInTheDocument()
      })
    })
  })
})
