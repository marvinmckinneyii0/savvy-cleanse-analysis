
import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import * as xml2js from 'xml2js';
import * as pdfjsLib from 'pdfjs-dist';

// Set up PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

export interface ParsedData {
  headers: string[];
  rows: any[][];
  totalRows: number;
  fileType: string;
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
        const rows = results.data.map((row: any) => 
          headers.map(header => row[header] || '')
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

const parseExcel = (file: File): Promise<ParseResult> => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: 'array' });
        
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];
        
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
        
        if (jsonData.length === 0) {
          resolve({
            success: false,
            error: 'Excel file appears to be empty'
          });
          return;
        }

        const headers = (jsonData[0] as any[]).map((header, index) => 
          header ? String(header) : `Column ${index + 1}`
        );
        const rows = jsonData.slice(1).map((row: any) => 
          headers.map((_, index) => row[index] || '')
        );

        resolve({
          success: true,
          data: {
            headers,
            rows,
            totalRows: rows.length,
            fileType: file.name.split('.').pop()?.toLowerCase() || 'excel'
          }
        });
      } catch (error) {
        resolve({
          success: false,
          error: `Excel parsing error: ${error instanceof Error ? error.message : 'Unknown error'}`
        });
      }
    };
    reader.readAsArrayBuffer(file);
  });
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
