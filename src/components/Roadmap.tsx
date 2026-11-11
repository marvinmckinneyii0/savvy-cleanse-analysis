import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DATA_SOURCES, DataSourceStatus } from '@/lib/dataSources';

const STATUS_CLASSES: Record<DataSourceStatus, string> = {
  'Available now': 'bg-savvy-gold text-white',
  Next: 'border border-savvy-gold text-savvy-gold',
  Planned: 'border border-muted-foreground/40 text-muted-foreground',
  Later: 'border border-muted-foreground/40 text-muted-foreground',
};

const Roadmap = () => (
  <section className="py-16 bg-white light-surface" id="roadmap">
    <div className="container px-4 md:px-6">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold">Data Sources Roadmap</h2>
        <p className="text-muted-foreground mt-3 max-w-2xl mx-auto">
          SAINT works with CSV files today. This is the order we plan to add more sources. It is an
          order, not a schedule.
        </p>
      </div>

      <ol className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {DATA_SOURCES.map((source, index) => (
          <li key={source.id}>
            <Card className="h-full shadow-sm hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="flex items-center justify-center w-8 h-8 rounded-full bg-savvy-gold text-white">
                    {index + 1}
                  </span>
                  <span className={`text-xs font-semibold rounded-full px-2 py-1 ${STATUS_CLASSES[source.status]}`}>
                    {source.status}
                  </span>
                </div>
                <CardTitle className="text-lg">{source.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-sm">{source.description}</p>
              </CardContent>
            </Card>
          </li>
        ))}
      </ol>
    </div>
  </section>
);

export default Roadmap;
