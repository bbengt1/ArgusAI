/**
 * SkipToContent Component Tests (Story P6-2.1)
 *
 * Tests for the skip to content accessibility link.
 *
 * Demonstrates:
 * - Testing accessibility attributes
 * - Testing sr-only/focus visibility behavior
 * - Testing anchor link target
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SkipToContent } from '@/components/layout/SkipToContent'

describe('SkipToContent', () => {
  describe('rendering', () => {
    it('renders a link element', () => {
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      expect(link).toBeInTheDocument()
    })

    it('has correct href attribute targeting main-content', () => {
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      expect(link).toHaveAttribute('href', '#main-content')
    })

    it('displays "Skip to content" text', () => {
      render(<SkipToContent />)

      expect(screen.getByText('Skip to content')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has sr-only class for screen reader visibility', () => {
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      expect(link).toHaveClass('sr-only')
    })

    it('has focus:not-sr-only class for visibility when focused', () => {
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      expect(link).toHaveClass('focus:not-sr-only')
    })

    it('has focus:absolute class for positioning when focused', () => {
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      expect(link).toHaveClass('focus:absolute')
    })

    it('has high z-index when focused to appear above other elements', () => {
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      expect(link).toHaveClass('focus:z-[100]')
    })
  })

  describe('styling', () => {
    it('has focus styling with primary background', () => {
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      expect(link).toHaveClass('focus:bg-primary')
    })

    it('has focus styling with primary foreground text', () => {
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      expect(link).toHaveClass('focus:text-primary-foreground')
    })

    it('has focus ring for accessibility indication', () => {
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      expect(link).toHaveClass('focus:ring-2')
      expect(link).toHaveClass('focus:ring-ring')
    })

    it('has rounded corners when focused', () => {
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      expect(link).toHaveClass('focus:rounded-md')
    })

    it('has padding when focused', () => {
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      expect(link).toHaveClass('focus:px-4')
      expect(link).toHaveClass('focus:py-2')
    })
  })

  describe('keyboard interaction', () => {
    it('can receive focus', async () => {
      const user = userEvent.setup()
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      await user.tab()

      expect(link).toHaveFocus()
    })

    it('is tabbable (in the tab order)', () => {
      render(<SkipToContent />)

      const link = screen.getByRole('link', { name: /skip to content/i })
      // Links are tabbable by default (tabIndex is 0 or not set)
      expect(link).not.toHaveAttribute('tabIndex', '-1')
    })
  })
})
