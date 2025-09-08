import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { Calendar, Clock, User, ArrowRight, BookOpen } from 'lucide-react';

const Blog = () => {
  const featuredPost = {
    title: "Why Formula Transparency Matters in AI Analytics",
    excerpt: "In an era where AI-driven analytics are becoming the norm, transparency isn't just a nice-to-have—it's essential for building trust and making informed decisions. Learn why SavvyClean shows you the math behind every insight.",
    author: "Sarah Chen",
    date: "December 15, 2024",
    readTime: "8 min read",
    category: "AI Ethics",
    image: "/placeholder.svg"
  };

  const posts = [
    {
      title: "From Data Chaos to Clarity: A Founder's Journey",
      excerpt: "The story behind SavvyClean's creation, from frustrating late nights cleaning messy datasets to building a platform that transforms how teams approach data analytics.",
      author: "Marcus Rodriguez",
      date: "December 10, 2024",
      readTime: "12 min read",
      category: "Company",
      tags: ["Startup", "Data Science", "Product"]
    },
    {
      title: "The Hidden Cost of Dirty Data in Business Analytics",
      excerpt: "Poor data quality costs organizations an average of $15 million per year. Discover the real impact of dirty data and proven strategies to address it.",
      author: "Dr. Emily Watson",
      date: "December 5, 2024",
      readTime: "6 min read",
      category: "Business",
      tags: ["Data Quality", "ROI", "Analytics"]
    },
    {
      title: "Democratizing Data Science: Making Analytics Accessible",
      excerpt: "How no-code analytics platforms are breaking down barriers and enabling business users to derive insights without technical expertise.",
      author: "James Liu",
      date: "November 28, 2024",
      readTime: "10 min read",
      category: "Technology",
      tags: ["No-Code", "Accessibility", "Business Intelligence"]
    },
    {
      title: "Predictive Analytics in Practice: Real-World Success Stories",
      excerpt: "Explore how companies across industries are using predictive analytics to optimize operations, reduce costs, and drive growth.",
      author: "Sarah Chen",
      date: "November 20, 2024",
      readTime: "9 min read",
      category: "Case Studies",
      tags: ["Predictive Analytics", "Machine Learning", "Success Stories"]
    },
    {
      title: "The Future of Data Cleaning: AI-Powered Automation",
      excerpt: "Machine learning is revolutionizing data preparation. Learn about the latest advances in automated data cleaning and what's coming next.",
      author: "Dr. Alex Kumar",
      date: "November 15, 2024",
      readTime: "7 min read",
      category: "Technology",
      tags: ["AI", "Automation", "Data Cleaning"]
    }
  ];

  const categories = [
    { name: "All Posts", count: 12 },
    { name: "Technology", count: 5 },
    { name: "Business", count: 4 },
    { name: "AI Ethics", count: 2 },
    { name: "Case Studies", count: 3 },
    { name: "Company", count: 2 }
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
                SavvyClean
                <span className="text-savvy-gold"> Blog</span>
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                Insights, tutorials, and thought leadership on data analytics, AI transparency, and the future of business intelligence.
              </p>
            </div>
          </div>
        </section>

        {/* Categories */}
        <section className="py-8 bg-white dark:bg-savvy-dark border-b">
          <div className="container px-4 md:px-6">
            <div className="flex flex-wrap gap-2 justify-center">
              {categories.map((category, index) => (
                <Button
                  key={index}
                  variant={index === 0 ? "default" : "ghost"}
                  size="sm"
                  className={index === 0 ? "bg-savvy-blue hover:bg-savvy-blue/90" : ""}
                >
                  {category.name} ({category.count})
                </Button>
              ))}
            </div>
          </div>
        </section>

        {/* Featured Post */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="max-w-4xl mx-auto">
              <Badge className="mb-4 bg-savvy-gold text-savvy-dark">Featured Post</Badge>
              <Card className="overflow-hidden shadow-lg">
                <div className="md:flex">
                  <div className="md:w-1/3">
                    <div className="h-48 md:h-full bg-gradient-to-br from-savvy-blue to-savvy-gold" />
                  </div>
                  <div className="md:w-2/3 p-8">
                    <Badge variant="secondary" className="mb-3">
                      {featuredPost.category}
                    </Badge>
                    <h2 className="text-2xl md:text-3xl font-bold mb-4">
                      {featuredPost.title}
                    </h2>
                    <p className="text-muted-foreground mb-6 leading-relaxed">
                      {featuredPost.excerpt}
                    </p>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mb-6">
                      <div className="flex items-center gap-1">
                        <User className="h-4 w-4" />
                        {featuredPost.author}
                      </div>
                      <div className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {featuredPost.date}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {featuredPost.readTime}
                      </div>
                    </div>
                    <Button className="bg-savvy-blue hover:bg-savvy-blue/90">
                      Read Full Article
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </section>

        {/* Recent Posts */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Recent Posts</h2>
              <p className="text-muted-foreground">
                Stay up to date with the latest insights from our team and the data analytics community.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
              {posts.map((post, index) => (
                <Card key={index} className="shadow-sm hover:shadow-lg transition-all duration-300 h-full">
                  <CardHeader>
                    <Badge variant="secondary" className="w-fit mb-2">
                      {post.category}
                    </Badge>
                    <CardTitle className="text-lg leading-tight">
                      {post.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex flex-col h-full">
                    <p className="text-muted-foreground mb-4 flex-grow leading-relaxed">
                      {post.excerpt}
                    </p>
                    
                    <div className="space-y-3">
                      <div className="flex flex-wrap gap-1">
                        {post.tags.map((tag, tagIndex) => (
                          <Badge key={tagIndex} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          {post.author}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {post.readTime}
                        </div>
                      </div>
                      
                      <div className="text-xs text-muted-foreground">
                        {post.date}
                      </div>
                    </div>
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
              <h2 className="text-3xl font-bold mb-4">Stay in the Loop</h2>
              <p className="text-gray-300 mb-8">
                Get the latest posts, tutorials, and insights delivered straight to your inbox. No spam, unsubscribe anytime.
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

export default Blog;