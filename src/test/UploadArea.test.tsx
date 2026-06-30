import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import UploadArea from '@/components/dashboard/UploadArea';

// parseFile is called for valid files; mock it so tests stay unit-scoped.
vi.mock('@/utils/fileParser', () => ({
  parseFile: vi.fn().mockResolvedValue({
    success: true,
    data: { headers: ['A'], rows: [['1']], totalRows: 1, fileType: 'xlsx' },
  }),
}));

// DataPreview renders after a successful parse; stub it out.
vi.mock('@/components/dashboard/DataPreview', () => ({
  default: () => <div data-testid="data-preview" />,
}));

const makeFile = (name: string) => new File(['content'], name);
const onFileUpload = vi.fn();

describe('UploadArea — .xls rejection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows the specific legacy-format message for a .xls file', async () => {
    render(<UploadArea onFileUpload={onFileUpload} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [makeFile('report.xls')] } });

    await waitFor(() => {
      expect(
        screen.getByText(/Legacy \.xls format isn't supported/i)
      ).toBeInTheDocument();
    });
  });

  it('does not call parseFile for a .xls file', async () => {
    const { parseFile } = await import('@/utils/fileParser');
    render(<UploadArea onFileUpload={onFileUpload} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [makeFile('report.xls')] } });

    await waitFor(() =>
      screen.getByText(/Legacy \.xls format isn't supported/i)
    );
    expect(parseFile).not.toHaveBeenCalled();
  });

  it('does not trigger onFileUpload for a .xls file', async () => {
    render(<UploadArea onFileUpload={onFileUpload} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [makeFile('report.xls')] } });

    await waitFor(() =>
      screen.getByText(/Legacy \.xls format isn't supported/i)
    );
    expect(onFileUpload).not.toHaveBeenCalled();
  });

  it('.xls rejection message differs from the generic unsupported-format message', async () => {
    render(<UploadArea onFileUpload={onFileUpload} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [makeFile('data.zzz')] } });

    await waitFor(() =>
      screen.getByText(/Unsupported file format/i)
    );
    expect(screen.queryByText(/Legacy \.xls/i)).not.toBeInTheDocument();
  });

  it('accept attribute does not list .xls', () => {
    render(<UploadArea onFileUpload={onFileUpload} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const accept = input.getAttribute('accept') ?? '';
    expect(accept).not.toMatch(/\.xls[^x]/); // .xls but not .xlsx
  });

  it('passes a .xlsx file through to parseFile without an error', async () => {
    const { parseFile } = await import('@/utils/fileParser');
    render(<UploadArea onFileUpload={onFileUpload} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [makeFile('report.xlsx')] } });

    await waitFor(() => expect(parseFile).toHaveBeenCalledTimes(1));
    expect(screen.queryByText(/Legacy \.xls/i)).not.toBeInTheDocument();
  });
});
