import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Download, Trash2, FileSpreadsheet, Eye } from 'lucide-react';
import { ParsedData } from '@/utils/fileParser';

export interface Dataset {
  id: string;
  file: File;
  parsedData: ParsedData;
  uploadedAt: Date;
}

interface DatasetManagerProps {
  datasets: Dataset[];
  activeDatasetId: string | null;
  onSelect: (id: string) => void;
  onRemove: (id: string) => void;
  onDownload: (dataset: Dataset) => void;
}

const DatasetManager: React.FC<DatasetManagerProps> = ({
  datasets,
  activeDatasetId,
  onSelect,
  onRemove,
  onDownload,
}) => {
  if (datasets.length === 0) return null;

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <FileSpreadsheet className="h-4 w-4" />
          Uploaded Datasets ({datasets.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>File Name</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Rows</TableHead>
                <TableHead>Uploaded</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {datasets.map((ds) => (
                <TableRow
                  key={ds.id}
                  className={activeDatasetId === ds.id ? 'bg-muted/50' : ''}
                >
                  <TableCell className="font-medium text-sm">
                    {ds.file.name}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatSize(ds.file.size)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {ds.parsedData.rows?.length ?? '—'}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {ds.uploadedAt.toLocaleTimeString()}
                  </TableCell>
                  <TableCell>
                    {activeDatasetId === ds.id ? (
                      <Badge variant="default" className="text-xs">Active</Badge>
                    ) : (
                      <Badge variant="secondary" className="text-xs">Ready</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onSelect(ds.id)}
                        title="View & Analyze"
                      >
                        <Eye className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDownload(ds)}
                        title="Download"
                      >
                        <Download className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onRemove(ds.id)}
                        title="Remove"
                      >
                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

export default DatasetManager;
