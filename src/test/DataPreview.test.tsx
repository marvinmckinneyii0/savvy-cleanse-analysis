import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import DataPreview from '@/components/dashboard/DataPreview';
import type { ParsedData } from '@/utils/fileParser';

const csvData = (rows: any[][]): ParsedData => ({
  headers: ['Name', 'Value'],
  rows,
  totalRows: rows.length,
  fileType: 'csv',
});

const xlsxData = (rows: any[][]): ParsedData => ({
  headers: ['Name', 'Value'],
  rows,
  totalRows: rows.length,
  fileType: 'xlsx',
  parseErrors: [],
});

describe('DataPreview — null cell rendering', () => {
  it('renders null cells as blank, not the literal string "null" (CSV source)', () => {
    render(<DataPreview data={csvData([['Alice', null]])} fileName="test.csv" />);
    const cells = screen.getAllByRole('cell');
    // cells[0] = "Alice", cells[1] = blank (null)
    expect(cells[1]).toHaveTextContent('');
    expect(cells[1].textContent).not.toBe('null');
  });

  it('renders undefined cells as blank (CSV source)', () => {
    render(<DataPreview data={csvData([['Alice', undefined]])} fileName="test.csv" />);
    const cells = screen.getAllByRole('cell');
    expect(cells[1]).toHaveTextContent('');
    expect(cells[1].textContent).not.toBe('undefined');
  });

  it('renders null cells as blank, not the literal string "null" (xlsx/backend source)', () => {
    render(<DataPreview data={xlsxData([['Bob', null]])} fileName="test.xlsx" />);
    const cells = screen.getAllByRole('cell');
    expect(cells[1]).toHaveTextContent('');
    expect(cells[1].textContent).not.toBe('null');
  });

  it('renders undefined cells as blank (xlsx/backend source)', () => {
    render(<DataPreview data={xlsxData([['Bob', undefined]])} fileName="test.xlsx" />);
    const cells = screen.getAllByRole('cell');
    expect(cells[1]).toHaveTextContent('');
    expect(cells[1].textContent).not.toBe('undefined');
  });

  it('still renders non-null values correctly', () => {
    render(<DataPreview data={csvData([['Alice', '42']])} fileName="test.csv" />);
    const cells = screen.getAllByRole('cell');
    expect(cells[0]).toHaveTextContent('Alice');
    expect(cells[1]).toHaveTextContent('42');
  });

  it('renders a mix of null and non-null cells in the same row', () => {
    render(<DataPreview data={csvData([['Alice', null], [null, '99']])} fileName="test.csv" />);
    const cells = screen.getAllByRole('cell');
    expect(cells[0]).toHaveTextContent('Alice');
    expect(cells[1]).toHaveTextContent('');
    expect(cells[2]).toHaveTextContent('');
    expect(cells[3]).toHaveTextContent('99');
  });
});
