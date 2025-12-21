/**
 * CameraDiscovery Component Tests
 *
 * Story P5-2.3: Build Camera Discovery UI with Add Action
 *
 * Tests:
 * - "Discover Cameras" button renders with correct icon
 * - Button disabled during active scan
 * - Loading spinner appears when scan starts
 * - Discovered camera list renders with device info
 * - "Already Added" badge for existing cameras
 * - Empty state renders when no devices found
 * - Error state and retry functionality
 * - 503 error handling (library not installed)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CameraDiscovery } from '@/components/cameras/CameraDiscovery';
import { apiClient } from '@/lib/api-client';
import type { ICamera } from '@/types/camera';
import type {
  IDiscoveryResponse,
  IDiscoveryStatusResponse,
  IDeviceDetailsResponse,
} from '@/types/discovery';

// Mock the API client
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    discovery: {
      status: vi.fn(),
      start: vi.fn(),
      getDeviceDetails: vi.fn(),
    },
  },
  ApiError: class ApiError extends Error {
    status: number;
    data: unknown;
    constructor(message: string, status: number = 500, data: unknown = null) {
      super(message);
      this.name = 'ApiError';
      this.status = status;
      this.data = data;
    }
  },
}));

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
}));

// Create a wrapper with QueryClientProvider
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
};

// Mock data
const mockDiscoveryStatusAvailable: IDiscoveryStatusResponse = {
  available: true,
  library_installed: true,
  message: 'ONVIF camera discovery is available',
};

const mockDiscoveryStatusUnavailable: IDiscoveryStatusResponse = {
  available: false,
  library_installed: false,
  message: 'WSDiscovery package not installed. Install with: pip install WSDiscovery',
};

const mockDiscoveryResponse: IDiscoveryResponse = {
  status: 'complete',
  duration_ms: 5000,
  devices: [
    {
      endpoint_url: 'http://192.168.1.100:80/onvif/device_service',
      scopes: ['onvif://www.onvif.org/type/NetworkVideoTransmitter'],
      types: ['tdn:NetworkVideoTransmitter'],
      metadata_version: '1',
    },
    {
      endpoint_url: 'http://192.168.1.101:80/onvif/device_service',
      scopes: ['onvif://www.onvif.org/type/NetworkVideoTransmitter'],
      types: ['tdn:NetworkVideoTransmitter'],
      metadata_version: '1',
    },
  ],
  device_count: 2,
  error_message: null,
};

const mockEmptyDiscoveryResponse: IDiscoveryResponse = {
  status: 'complete',
  duration_ms: 10000,
  devices: [],
  device_count: 0,
  error_message: null,
};

const mockDeviceDetailsResponse: IDeviceDetailsResponse = {
  status: 'success',
  device: {
    id: 'camera-192-168-1-100-80',
    endpoint_url: 'http://192.168.1.100:80/onvif/device_service',
    ip_address: '192.168.1.100',
    port: 80,
    device_info: {
      name: 'Front Door Camera',
      manufacturer: 'Dahua',
      model: 'IPC-HDW2431T',
      firmware_version: '2.800.0000000.44.R',
      serial_number: '6G12345678',
      hardware_id: '1.0',
    },
    profiles: [
      {
        name: 'mainStream',
        token: 'profile_token_1',
        resolution: '2688x1520',
        width: 2688,
        height: 1520,
        fps: 25,
        rtsp_url: 'rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=0',
        encoding: 'H264',
      },
      {
        name: 'subStream',
        token: 'profile_token_2',
        resolution: '704x480',
        width: 704,
        height: 480,
        fps: 25,
        rtsp_url: 'rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=1',
        encoding: 'H264',
      },
    ],
    primary_rtsp_url: 'rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=0',
    requires_auth: false,
    discovered_at: new Date().toISOString(),
  },
  error_message: null,
  duration_ms: 1234,
};

const mockExistingCameras: ICamera[] = [
  {
    id: 'existing-camera-1',
    name: 'Existing Camera',
    type: 'rtsp',
    rtsp_url: 'rtsp://192.168.1.101:554/stream1',
    frame_rate: 5,
    is_enabled: true,
    motion_enabled: true,
    motion_sensitivity: 'medium',
    motion_cooldown: 30,
    motion_algorithm: 'mog2',
    source_type: 'rtsp',
    analysis_mode: 'single_frame',
    homekit_stream_quality: 'high',
    audio_enabled: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

describe('CameraDiscovery', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default to available status
    vi.mocked(apiClient.discovery.status).mockResolvedValue(mockDiscoveryStatusAvailable);
  });

  describe('Initial Render', () => {
    it('renders "Discover Cameras" button with Radar icon', async () => {
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      const button = await screen.findByRole('button', { name: /discover cameras/i });
      expect(button).toBeInTheDocument();
      // Check for Radar icon (Lucide icons render as SVG)
      expect(button.querySelector('svg')).toBeInTheDocument();
    });

    it('renders title and description', async () => {
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      expect(await screen.findByText('ONVIF Camera Discovery')).toBeInTheDocument();
      expect(screen.getByText(/scan your network for onvif-compatible cameras/i)).toBeInTheDocument();
    });
  });

  describe('Discovery Unavailable', () => {
    it('disables button when discovery is unavailable', async () => {
      vi.mocked(apiClient.discovery.status).mockResolvedValue(mockDiscoveryStatusUnavailable);

      render(<CameraDiscovery />, { wrapper: createWrapper() });

      // Wait for the unavailable warning message to appear (indicates status query completed)
      await waitFor(() => {
        expect(screen.getByText('Camera Discovery Unavailable')).toBeInTheDocument();
      });

      // Now check button is disabled
      const button = screen.getByRole('button', { name: /discover cameras/i });
      expect(button).toBeDisabled();
    });

    it('shows warning message when discovery is unavailable', async () => {
      vi.mocked(apiClient.discovery.status).mockResolvedValue(mockDiscoveryStatusUnavailable);

      render(<CameraDiscovery />, { wrapper: createWrapper() });

      expect(await screen.findByText('Camera Discovery Unavailable')).toBeInTheDocument();
      expect(screen.getByText(/wsdiscovery package not installed/i)).toBeInTheDocument();
    });
  });

  describe('Scanning State', () => {
    it('disables button and shows loading state during scan', async () => {
      // Make startScan take a while
      vi.mocked(apiClient.discovery.start).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockDiscoveryResponse), 1000))
      );

      const user = userEvent.setup();
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      const button = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(button);

      // Button should show "Scanning..." and be disabled
      expect(await screen.findByRole('button', { name: /scanning/i })).toBeDisabled();
      expect(screen.getByText(/scanning network for cameras/i)).toBeInTheDocument();
    });

    it('shows progress message during scan', async () => {
      vi.mocked(apiClient.discovery.start).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockDiscoveryResponse), 1000))
      );

      const user = userEvent.setup();
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      const button = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(button);

      expect(await screen.findByText(/this may take up to 10 seconds/i)).toBeInTheDocument();
    });
  });

  describe('Discovery Results', () => {
    it('displays discovered cameras after successful scan', async () => {
      vi.mocked(apiClient.discovery.start).mockResolvedValue(mockDiscoveryResponse);
      vi.mocked(apiClient.discovery.getDeviceDetails).mockResolvedValue(mockDeviceDetailsResponse);

      const user = userEvent.setup();
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      const button = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(button);

      // Wait for results to appear
      await waitFor(() => {
        expect(screen.getByText(/found 2 camera/i)).toBeInTheDocument();
      });
    });

    it('shows camera details after fetching', async () => {
      vi.mocked(apiClient.discovery.start).mockResolvedValue({
        ...mockDiscoveryResponse,
        devices: [mockDiscoveryResponse.devices[0]], // Just one device
        device_count: 1,
      });
      vi.mocked(apiClient.discovery.getDeviceDetails).mockResolvedValue(mockDeviceDetailsResponse);

      const user = userEvent.setup();
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      const button = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(button);

      // Wait for device details to load
      await waitFor(() => {
        expect(screen.getByText('Front Door Camera')).toBeInTheDocument();
      });
      expect(screen.getByText('Dahua')).toBeInTheDocument();
      expect(screen.getByText('192.168.1.100')).toBeInTheDocument();
    });

    it('shows "Already Added" badge for existing cameras', async () => {
      // Create a device details response with IP matching existing camera
      const mockDeviceDetailsForExisting: IDeviceDetailsResponse = {
        status: 'success',
        device: {
          id: 'camera-192-168-1-101-80',
          endpoint_url: 'http://192.168.1.101:80/onvif/device_service',
          ip_address: '192.168.1.101', // Matches existing camera in mockExistingCameras
          port: 80,
          device_info: {
            name: 'Existing Camera ONVIF',
            manufacturer: 'TestCam',
            model: 'TC-100',
            firmware_version: '1.0.0',
            serial_number: 'TC123',
            hardware_id: '1.0',
          },
          profiles: [{
            name: 'mainStream',
            token: 'token1',
            resolution: '1920x1080',
            width: 1920,
            height: 1080,
            fps: 30,
            rtsp_url: 'rtsp://192.168.1.101:554/stream1',
            encoding: 'H264',
          }],
          primary_rtsp_url: 'rtsp://192.168.1.101:554/stream1',
          requires_auth: false,
          discovered_at: new Date().toISOString(),
        },
        error_message: null,
        duration_ms: 500,
      };

      // Return just the device at 192.168.1.101
      vi.mocked(apiClient.discovery.start).mockResolvedValue({
        status: 'complete',
        duration_ms: 5000,
        devices: [{
          endpoint_url: 'http://192.168.1.101:80/onvif/device_service',
          scopes: ['onvif://www.onvif.org/type/NetworkVideoTransmitter'],
          types: ['tdn:NetworkVideoTransmitter'],
          metadata_version: '1',
        }],
        device_count: 1,
        error_message: null,
      });
      vi.mocked(apiClient.discovery.getDeviceDetails).mockResolvedValue(mockDeviceDetailsForExisting);

      const user = userEvent.setup();
      render(<CameraDiscovery existingCameras={mockExistingCameras} />, { wrapper: createWrapper() });

      const button = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(button);

      // Wait for device details to load and check for "Already Added" badge
      // The badge appears twice: once in badge, once in button - use getAllByText
      await waitFor(() => {
        const alreadyAddedElements = screen.getAllByText('Already Added');
        expect(alreadyAddedElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no cameras found', async () => {
      vi.mocked(apiClient.discovery.start).mockResolvedValue(mockEmptyDiscoveryResponse);

      const user = userEvent.setup();
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      const button = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(button);

      // Wait for empty state
      await waitFor(() => {
        expect(screen.getByText('No ONVIF Cameras Found')).toBeInTheDocument();
      });
    });

    it('shows guidance in empty state', async () => {
      vi.mocked(apiClient.discovery.start).mockResolvedValue(mockEmptyDiscoveryResponse);

      const user = userEvent.setup();
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      const button = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText(/don't support onvif/i)).toBeInTheDocument();
      });
    });

    it('shows retry button in empty state', async () => {
      vi.mocked(apiClient.discovery.start).mockResolvedValue(mockEmptyDiscoveryResponse);

      const user = userEvent.setup();
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      const discoverButton = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(discoverButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });
    });

    it('shows manual entry link in empty state', async () => {
      vi.mocked(apiClient.discovery.start).mockResolvedValue(mockEmptyDiscoveryResponse);

      const user = userEvent.setup();
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      const button = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /add manually/i })).toBeInTheDocument();
      });
    });
  });

  describe('Error State', () => {
    it('shows error state when discovery fails', async () => {
      vi.mocked(apiClient.discovery.start).mockRejectedValue(
        new Error('Network error')
      );

      const user = userEvent.setup();
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      const button = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText('Discovery Failed')).toBeInTheDocument();
      });
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('shows retry button in error state', async () => {
      vi.mocked(apiClient.discovery.start).mockRejectedValue(
        new Error('Network error')
      );

      const user = userEvent.setup();
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      const discoverButton = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(discoverButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry scan/i })).toBeInTheDocument();
      });
    });

    it('can retry after error', async () => {
      vi.mocked(apiClient.discovery.start)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockDiscoveryResponse);
      vi.mocked(apiClient.discovery.getDeviceDetails).mockResolvedValue(mockDeviceDetailsResponse);

      const user = userEvent.setup();
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      // First attempt fails
      const discoverButton = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(discoverButton);

      await waitFor(() => {
        expect(screen.getByText('Discovery Failed')).toBeInTheDocument();
      });

      // Retry succeeds
      const retryButton = screen.getByRole('button', { name: /retry scan/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText(/found 2 camera/i)).toBeInTheDocument();
      });
    });
  });

  describe('Rescan', () => {
    it('shows rescan button after successful scan', async () => {
      vi.mocked(apiClient.discovery.start).mockResolvedValue(mockDiscoveryResponse);
      vi.mocked(apiClient.discovery.getDeviceDetails).mockResolvedValue(mockDeviceDetailsResponse);

      const user = userEvent.setup();
      render(<CameraDiscovery />, { wrapper: createWrapper() });

      const button = await screen.findByRole('button', { name: /discover cameras/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /rescan/i })).toBeInTheDocument();
      });
    });
  });
});
