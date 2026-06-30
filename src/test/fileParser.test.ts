import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { parseFile } from '@/utils/fileParser';

// pdf.js uses a CDN worker URL that can't resolve in jsdom — stub the whole module.
vi.mock('pdfjs-dist', () => ({
  GlobalWorkerOptions: { workerSrc: '' },
  getDocument: vi.fn(),
  version: '3.0.0',
}));

const makeXlsxFile = (name = 'data.xlsx') => new File(['<binary>'], name);

const mockFetch = (overrides: Partial<Response> = {}) => {
  const defaults: Response = {
    ok: true,
    status: 200,
    statusText: 'OK',
    json: async () => ({
      headers: ['Name', 'Score'],
      rows: [['Alice', 95], ['Bob', null]],
      total_rows: 2,
      file_type: 'xlsx',
      parse_errors: [],
    }),
  } as unknown as Response;

  return vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ...defaults, ...overrides } as Response);
};

describe('parseExcel() — fetch path', () => {
  afterEach(() => vi.restoreAllMocks());

  it('POSTs multipart/form-data to /api/parse-file', async () => {
    const spy = mockFetch();
    await parseFile(makeXlsxFile());

    expect(spy).toHaveBeenCalledTimes(1);
    const [url, init] = spy.mock.calls[0];
    expect(url).toBe('/api/parse-file');
    expect(init?.method).toBe('POST');
    expect(init?.body).toBeInstanceOf(FormData);
  });

  it('attaches the file to the FormData body', async () => {
    const spy = mockFetch();
    const file = makeXlsxFile('report.xlsx');
    await parseFile(file);

    const formData = spy.mock.calls[0][1]?.body as FormData;
    expect(formData.get('file')).toBe(file);
  });

  it('maps a successful response into ParsedData', async () => {
    mockFetch();
    const result = await parseFile(makeXlsxFile());

    expect(result.success).toBe(true);
    expect(result.data?.headers).toEqual(['Name', 'Score']);
    expect(result.data?.rows).toEqual([['Alice', 95], ['Bob', null]]);
    expect(result.data?.totalRows).toBe(2);
    expect(result.data?.fileType).toBe('xlsx');
  });

  it('surfaces parseErrors[] from the response', async () => {
    mockFetch({
      json: async () => ({
        headers: ['Formula'],
        rows: [[null]],
        total_rows: 1,
        file_type: 'xlsx',
        parse_errors: [{ row: 0, column: 'Formula', issue: 'formula_cell', raw_value: '=SUM(A1)' }],
      }),
    } as unknown as Response);

    const result = await parseFile(makeXlsxFile());

    expect(result.data?.parseErrors).toHaveLength(1);
    expect(result.data?.parseErrors![0]).toMatchObject({
      row: 0,
      column: 'Formula',
      issue: 'formula_cell',
      rawValue: '=SUM(A1)',
    });
  });

  it('returns success: false (not throws) on a 400 response', async () => {
    mockFetch({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: async () => ({ detail: 'Unsupported file format. Only .xlsx and .xlsm are accepted.' }),
    } as unknown as Response);

    const result = await parseFile(makeXlsxFile());

    expect(result.success).toBe(false);
    expect(result.error).toMatch(/Unsupported file format/i);
  });

  it('returns success: false (not throws) when fetch rejects', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Network failure'));

    const result = await parseFile(makeXlsxFile());

    expect(result.success).toBe(false);
    expect(result.error).toMatch(/Network failure/);
  });
});
