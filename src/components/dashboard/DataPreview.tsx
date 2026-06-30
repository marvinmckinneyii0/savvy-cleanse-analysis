
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, FileText } from 'lucide-react';
import { ParsedData } from '@/utils/fileParser';

interface DataPreviewProps {
  data: ParsedData;
  fileName: string;
}

const DataPreview: React.FC<DataPreviewProps> = ({ data, fileName }) => {
  const previewRows = data.rows.slice(0, 5);

  return (
    <Card className="w-full mt-4">
      <CardHeader>
        <div className="flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-green-500" />
          <CardTitle className="text-lg">Data Preview</CardTitle>
        </div>
        <CardDescription>
          Successfully parsed {fileName} ({data.fileType.toUpperCase()}) - 
          Showing {previewRows.length} of {data.totalRows} rows
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                {data.headers.map((header, index) => (
                  <TableHead key={index} className="font-medium">
                    {header}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {previewRows.map((row, rowIndex) => (
                <TableRow key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <TableCell key={cellIndex} className="max-w-xs truncate">
                      {cell === null || cell === undefined ? '' : String(cell)}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        
        {data.totalRows > 5 && (
          <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
            <FileText className="h-4 w-4" />
            <span>
              {data.totalRows - 5} more rows available for analysis
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DataPreview;
