/**
 * Data sources SAINT accepts today and plans to accept, in the order they are
 * planned. The order and its reasons are in
 * _bmad-output/planning-artifacts/data-source-roadmap.md. No dates are given:
 * none is committed.
 */
export type DataSourceStatus = 'Available now' | 'Next' | 'Planned' | 'Later';

export interface DataSource {
  id: string;
  name: string;
  status: DataSourceStatus;
  description: string;
}

export const DATA_SOURCES: DataSource[] = [
  {
    id: 'csv',
    name: 'CSV files',
    status: 'Available now',
    description: 'Send a CSV of up to 100 MB and get a written data-quality report back.',
  },
  {
    id: 'excel',
    name: 'Excel workbooks',
    status: 'Next',
    description:
      'Modern Excel files (.xlsx). SAINT can already read them; they need to be connected to the report.',
  },
  {
    id: 'json',
    name: 'JSON files',
    status: 'Planned',
    description: 'Table-shaped JSON, such as exports from web tools, flattened into rows and columns.',
  },
  {
    id: 'api',
    name: 'Connections to your tools',
    status: 'Planned',
    description:
      'Pull data straight from the systems you already use, so reports can run without a file. This arrives with accounts and the web app.',
  },
  {
    id: 'documents',
    name: 'Documents and AI search (RAG)',
    status: 'Later',
    description:
      'Bring in PDFs and other documents and ask questions about them. This comes last because it needs accuracy checks before it can be trusted.',
  },
];

/** Upcoming items a visitor can register interest in. */
export const INTEREST_OPTIONS = [
  ...DATA_SOURCES.filter((source) => source.status !== 'Available now').map((source) => ({
    id: source.id,
    label: source.name,
  })),
  { id: 'web-app', label: 'Self-serve web app' },
];
