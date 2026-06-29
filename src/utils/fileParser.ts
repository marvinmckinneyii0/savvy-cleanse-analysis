
import Papa from 'papaparse';
import * as xml2js from 'xml2js';
import * as pdfjsLib from 'pdfjs-dist';

// Set up PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

// A cell the backend parser could not represent faithfully (an Excel error
// literal, or a formula with no cached result). Surfaced rather than dropped,
// mirroring the backend CellParseError contract — see
// backend/models/parsed_file.py.
export interface ParseError {
  row: number;
  column: string;
  issue: 'formula_cell' | 'error_cell';
  rawValue: string;
}

export interface ParsedData {
  headers: string[];
  rows: any[][];
  totalRows: number;
  fileType: string;
  // Present only for spreadsheet uploads parsed server-side; undefined for the
  // client-side formats below. Optional so existing consumers stay valid.
  parseErrors?: ParseError[];
}

export interface ParseResult {
  success: boolean;
  data?: ParsedData;
  error?: string;
}

export const parseFile = async (file: File): Promise<ParseResult> => {
  const fileExtension = file.name.split('.').pop()?.toLowerCase();
  
  try {
    switch (fileExtension) {
      case 'csv':
        return await parseCSV(file);
      case 'txt':
        return await parseTXT(file);
      case 'json':
        return await parseJSON(file);
      case 'xls':
      case 'xlsx':
        return await parseExcel(file);
      case 'xml':
        return await parseXML(file);
      case 'pdf':
        return await parsePDF(file);
      default:
        return {
          success: false,
          error: `Unsupported file format: ${fileExtension}`
        };
    }
  } catch (error) {
    return {
      success: false,
      error: `Failed to parse file: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
};

const parseCSV = (file: File): Promise<ParseResult> => {
  return new Promise((resolve) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        if (results.errors.length > 0) {
          resolve({
            success: false,
            error: `CSV parsing error: ${results.errors[0].message}`
          });
          return;
        }

        const headers = results.meta.fields || [];
        // Preserve empty cells as null (detect-don't-fix) rather than coercing
        // to '' — the parse layer must not silently rewrite missing values.
        const rows = results.data.map((row: any) =>
          headers.map(header => row[header] ?? null)
        );

        resolve({
          success: true,
          data: {
            headers,
            rows,
            totalRows: rows.length,
            fileType: 'csv'
          }
        });
      },
      error: (error) => {
        resolve({
          success: false,
          error: `CSV parsing error: ${error.message}`
        });
      }
    });
  });
};

const parseTXT = (file: File): Promise<ParseResult> => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const lines = content.split('\n').filter(line => line.trim() !== '');
        
        // Try to detect if it's CSV-like
        const firstLine = lines[0];
        if (firstLine && (firstLine.includes(',') || firstLine.includes('\t'))) {
          Papa.parse(content, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
              const headers = results.meta.fields || [];
              const rows = results.data.map((row: any) => 
                headers.map(header => row[header] || '')
              );

              resolve({
                success: true,
                data: {
                  headers,
                  rows,
                  totalRows: rows.length,
                  fileType: 'txt'
                }
              });
            }
          });
        } else {
          // Treat as plain text
          const headers = ['Line', 'Content'];
          const rows = lines.map((line, index) => [index + 1, line]);

          resolve({
            success: true,
            data: {
              headers,
              rows,
              totalRows: rows.length,
              fileType: 'txt'
            }
          });
        }
      } catch (error) {
        resolve({
          success: false,
          error: `Text file parsing error: ${error instanceof Error ? error.message : 'Unknown error'}`
        });
      }
    };
    reader.readAsText(file);
  });
};

const parseJSON = (file: File): Promise<ParseResult> => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const jsonData = JSON.parse(content);
        
        let headers: string[] = [];
        let rows: any[][] = [];

        if (Array.isArray(jsonData)) {
          if (jsonData.length > 0 && typeof jsonData[0] === 'object') {
            headers = Object.keys(jsonData[0]);
            rows = jsonData.map(item => 
              headers.map(header => item[header] || '')
            );
          } else {
            headers = ['Index', 'Value'];
            rows = jsonData.map((item, index) => [index, JSON.stringify(item)]);
          }
        } else if (typeof jsonData === 'object') {
          headers = ['Key', 'Value'];
          rows = Object.entries(jsonData).map(([key, value]) => [
            key, 
            typeof value === 'object' ? JSON.stringify(value) : value
          ]);
        }

        resolve({
          success: true,
          data: {
            headers,
            rows,
            totalRows: rows.length,
            fileType: 'json'
          }
        });
      } catch (error) {
        resolve({
          success: false,
          error: `JSON parsing error: ${error instanceof Error ? error.message : 'Invalid JSON format'}`
        });
      }
    };
    reader.readAsText(file);
  });
};

// Shape returned by POST /api/parse-file (snake_case JSON from the FastAPI
// backend). Mapped to ParsedData below.
interface ParsedFileResponse {
  headers: string[];
  rows: any[][];
  total_rows: number;
  file_type: string;
  parse_errors: { row: number; column: string; issue: 'formula_cell' | 'error_cell'; raw_value: string }[];
}

// Spreadsheet parsing moved server-side: the browser-side `xlsx` (SheetJS)
// package was removed to clear two HIGH advisories (GHSA-4r6h-8v6p-xvw6,
// GHSA-5pgg-2g8v-p4x9). The raw file is POSTed to the backend, which parses it
// with openpyxl (null-preserving, no pandas coercion) and returns ParsedData.
const parseExcel = async (file: File): Promise<ParseResult> => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/parse-file', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      // FastAPI returns { detail: "..." } on 4xx; fall back to status text.
      let detail = response.statusText;
      try {
        const body = await response.json();
        if (body?.detail) detail = body.detail;
      } catch {
        // non-JSON error body; keep statusText
      }
      return { success: false, error: `Excel parsing error: ${detail}` };
    }

    const payload = (await response.json()) as ParsedFileResponse;

    return {
      success: true,
      data: {
        headers: payload.headers,
        rows: payload.rows,
        totalRows: payload.total_rows,
        fileType: payload.file_type,
        parseErrors: payload.parse_errors.map((e) => ({
          row: e.row,
          column: e.column,
          issue: e.issue,
          rawValue: e.raw_value,
        })),
      },
    };
  } catch (error) {
    return {
      success: false,
      error: `Excel parsing error: ${error instanceof Error ? error.message : 'Unknown error'}`,
    };
  }
};

const parseXML = (file: File): Promise<ParseResult> => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        xml2js.parseString(content, (err, result) => {
          if (err) {
            resolve({
              success: false,
              error: `XML parsing error: ${err.message}`
            });
            return;
          }

          const flattenObject = (obj: any, prefix = ''): any => {
            let flattened: any = {};
            for (let key in obj) {
              if (typeof obj[key] === 'object' && obj[key] !== null) {
                if (Array.isArray(obj[key])) {
                  obj[key].forEach((item: any, index: number) => {
                    if (typeof item === 'object') {
                      Object.assign(flattened, flattenObject(item, `${prefix}${key}[${index}].`));
                    } else {
                      flattened[`${prefix}${key}[${index}]`] = item;
                    }
                  });
                } else {
                  Object.assign(flattened, flattenObject(obj[key], `${prefix}${key}.`));
                }
              } else {
                flattened[`${prefix}${key}`] = obj[key];
              }
            }
            return flattened;
          };

          const flattened = flattenObject(result);
          const headers = Object.keys(flattened);
          const rows = [Object.values(flattened)];

          resolve({
            success: true,
            data: {
              headers,
              rows,
              totalRows: rows.length,
              fileType: 'xml'
            }
          });
        });
      } catch (error) {
        resolve({
          success: false,
          error: `XML parsing error: ${error instanceof Error ? error.message : 'Unknown error'}`
        });
      }
    };
    reader.readAsText(file);
  });
};

const parsePDF = async (file: File): Promise<ParseResult> => {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    
    let fullText = '';
    
    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
      const page = await pdf.getPage(pageNum);
      const textContent = await page.getTextContent();
      const pageText = textContent.items
        .map((item: any) => item.str)
        .join(' ');
      fullText += pageText + '\n';
    }

    const lines = fullText.split('\n').filter(line => line.trim() !== '');
    const headers = ['Page Section', 'Content'];
    const rows = lines.map((line, index) => [
      `Section ${index + 1}`,
      line.trim()
    ]);

    return {
      success: true,
      data: {
        headers,
        rows,
        totalRows: rows.length,
        fileType: 'pdf'
      }
    };
  } catch (error) {
    return {
      success: false,
      error: `PDF parsing error: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
};
