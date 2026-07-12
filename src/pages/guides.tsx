import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { BookOpen, Clock, User, TrendingUp, FileText, BarChart } from 'lucide-react';

const Guides = () => {
  const guides = [
    {
      title: "Cleaning Messy CSVs",
      description: "A comprehensive step-by-step guide on handling missing values, duplicates, and inconsistent data formatting in CSV files.",
      duration: "15 min read",
      level: "Beginner",
      category: "Data Cleaning",
      icon: <FileText className="h-6 w-6 text-savvy-blue" />,
      topics: [
        "Identifying data quality issues",
        "Handling missing values with different strategies",
        "Detecting and removing duplicates",
        "Standardizing data formats",
        "Validating cleaned results"
      ]
    },
    {
      title: "Predictive Analytics with SAINT",
      description: "Learn how to use SAINT's built-in regression models to forecast sales, predict customer behavior, and identify trends.",
      duration: "25 min read",
      level: "Intermediate",
      category: "Analytics",
      icon: <TrendingUp className="h-6 w-6 text-savvy-gold" />,
      topics: [
        "Understanding predictive modeling",
        "Preparing data for predictions",
        "Selecting the right regression model",
        "Interpreting model results and statistics",
        "Exporting models for production use"
      ]
    }
  ];

  const upcomingGuides = [
    {
      title: "Advanced Data Transformations",
      category: "Data Processing",
      status: "Coming Soon"
    },
    {
      title: "Building Custom Dashboards",
      category: "Visualization",
      status: "Coming Soon"
    },
    {
      title: "API Integration Best Practices",
      category: "Development",
      status: "Coming Soon"
    },
    {
      title: "NLP Analysis Workflows",
      category: "Text Analytics",
      status: "Coming Soon"
    }
  ];

  const categories = [
    { name: "Data Cleaning", count: 8, color: "bg-savvy-blue" },
    { name: "Analytics", count: 6, color: "bg-savvy-gold" },
    { name: "Visualization", count: 4, color: "bg-savvy-blue" },
    { name: "Integration", count: 3, color: "bg-savvy-gold" }
  ];

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-4xl mx-auto">
              <BookOpen className="h-16 w-16 text-savvy-gold mx-auto mb-6" />
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                Learning
                <span className="text-savvy-gold"> Guides</span>
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                Master data analytics with our comprehensive, step-by-step guides written by industry experts.
              </p>
            </div>
          </div>
        </section>

        {/* Categories */}
        <section className="py-12 bg-white dark:bg-savvy-dark border-b">
          <div className="container px-4 md:px-6">
            <div className="flex flex-wrap gap-4 justify-center">
              {categories.map((category, index) => (
                <div key={index} className="flex items-center gap-2 bg-card rounded-full px-4 py-2 border">
                  <div className={`w-3 h-3 rounded-full ${category.color}`} />
                  <span className="font-medium">{category.name}</span>
                  <Badge variant="secondary" className="text-xs">
                    {category.count}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Featured Guides */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Featured Guides</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                In-depth tutorials to help you master the most important data analytics workflows.
              </p>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
              {guides.map((guide, index) => (
                <Card key={index} className="shadow-sm hover:shadow-lg transition-all duration-300 h-full">
                  <CardHeader>
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        {guide.icon}
                        <Badge variant="secondary">{guide.category}</Badge>
                      </div>
                      <Badge variant="outline">{guide.level}</Badge>
                    </div>
                    <CardTitle className="text-xl mb-2">{guide.title}</CardTitle>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {guide.duration}
                      </div>
                      <div className="flex items-center gap-1">
                        <User className="h-4 w-4" />
                        {guide.level}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground mb-6 leading-relaxed">
                      {guide.description}
                    </p>
                    
                    <div className="mb-6">
                      <h4 className="font-semibold mb-3">What you'll learn:</h4>
                      <ul className="space-y-2">
                        {guide.topics.map((topic, topicIndex) => (
                          <li key={topicIndex} className="text-sm text-muted-foreground flex items-start">
                            <span className="text-savvy-blue mr-2">•</span>
                            {topic}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    <Button className="w-full">Read Guide</Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Upcoming Guides */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Coming Soon</h2>
              <p className="text-muted-foreground">
                More comprehensive guides are in development. Stay tuned for updates!
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 max-w-4xl mx-auto">
              {upcomingGuides.map((guide, index) => (
                <Card key={index} className="shadow-sm border-dashed">
                  <CardContent className="p-4 text-center">
                    <BarChart className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                    <h3 className="font-semibold mb-2">{guide.title}</h3>
                    <Badge variant="secondary" className="mb-2">
                      {guide.category}
                    </Badge>
                    <p className="text-xs text-muted-foreground">{guide.status}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Newsletter Signup */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold mb-4">Stay Updated</h2>
              <p className="text-gray-300 mb-8">
                Get notified when we publish new guides and tutorials. Join our learning community.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center max-w-md mx-auto">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="flex-1 px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-savvy-gold"
                />
                <Button className="bg-savvy-gold text-savvy-dark hover:bg-savvy-gold/90 px-8">
                  Subscribe
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Guides;