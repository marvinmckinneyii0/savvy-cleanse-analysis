import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { MapPin, Clock, Users, Briefcase, Heart, Zap, Globe, Mail } from 'lucide-react';

const Careers = () => {
  const positions = [
    {
      title: "Data Engineer",
      location: "Remote",
      type: "Full-time",
      department: "Engineering",
      description: "Build robust data pipelines to support our cleaning and analytics platform. Work with cutting-edge technologies to process millions of rows of data daily.",
      requirements: [
        "3+ years experience with Python and SQL",
        "Experience with cloud platforms (AWS, GCP, or Azure)",
        "Knowledge of data pipeline tools (Airflow, Kafka, etc.)",
        "Understanding of data warehouse concepts",
        "Strong problem-solving skills"
      ],
      responsibilities: [
        "Design and implement scalable data processing pipelines",
        "Optimize data storage and retrieval systems",
        "Collaborate with ML engineers on model deployment",
        "Monitor and maintain data infrastructure",
        "Contribute to architectural decisions"
      ],
      email: "careers@savvyanalytics.info"
    },
    {
      title: "Full-Stack Engineer",
      location: "Remote",
      type: "Full-time", 
      department: "Engineering",
      description: "Extend the SavvyClean platform with new features and integrations. Work across our React frontend and Python backend to deliver exceptional user experiences.",
      requirements: [
        "4+ years full-stack development experience",
        "Proficiency in React, TypeScript, and Python",
        "Experience with REST APIs and database design",
        "Knowledge of cloud deployment and DevOps",
        "Passion for clean, maintainable code"
      ],
      responsibilities: [
        "Develop new product features end-to-end",
        "Build and maintain API integrations",
        "Optimize application performance and scalability",
        "Collaborate with design team on UI/UX improvements",
        "Participate in code reviews and technical planning"
      ],
      email: "careers@savvyanalytics.info"
    },
    {
      title: "AI Research Intern",
      location: "Remote",
      type: "Internship",
      department: "Research",
      description: "Experiment with cutting-edge analytics models and contribute to our research initiatives. Perfect for students or recent graduates passionate about AI and data science.",
      requirements: [
        "Currently pursuing or recently completed degree in CS, Statistics, or related field",
        "Strong foundation in machine learning and statistics",
        "Experience with Python, pandas, and scikit-learn",
        "Familiarity with deep learning frameworks (PyTorch, TensorFlow)",
        "Excellent research and communication skills"
      ],
      responsibilities: [
        "Research and implement new analytics algorithms",
        "Experiment with novel data cleaning techniques",
        "Contribute to technical blog posts and documentation",
        "Collaborate with engineering team on model integration",
        "Present findings to leadership team"
      ],
      email: "careers@savvyanalytics.info"
    }
  ];

  const benefits = [
    {
      icon: <Globe className="h-6 w-6 text-savvy-blue" />,
      title: "Remote-First Culture",
      description: "Work from anywhere with flexible hours and async collaboration"
    },
    {
      icon: <Heart className="h-6 w-6 text-savvy-gold" />,
      title: "Health & Wellness",
      description: "Comprehensive health insurance and wellness stipend"
    },
    {
      icon: <Zap className="h-6 w-6 text-savvy-blue" />,
      title: "Professional Growth",
      description: "Learning budget, conference attendance, and mentorship programs"
    },
    {
      icon: <Users className="h-6 w-6 text-savvy-gold" />,
      title: "Equity & Ownership",
      description: "Meaningful equity stake in the company's success"
    }
  ];

  const values = [
    "Transparency in everything we do",
    "Continuous learning and growth",
    "Work-life balance and mental health",
    "Diversity, equity, and inclusion",
    "Customer-centric thinking",
    "Technical excellence and innovation"
  ];

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-4xl mx-auto">
              <Briefcase className="h-16 w-16 text-savvy-gold mx-auto mb-6" />
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                Join Our
                <span className="text-savvy-gold"> Mission</span>
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-8">
                Help us democratize data analytics and build tools that turn chaos into clarity. We're looking for passionate individuals who want to make a real impact.
              </p>
              <Badge className="bg-savvy-gold/20 text-savvy-gold border-savvy-gold/30">
                Remote-First • Global Team • Meaningful Work
              </Badge>
            </div>
          </div>
        </section>

        {/* Open Positions */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Open Positions</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                We're growing our team and looking for talented individuals who share our passion for transparent, accessible analytics.
              </p>
            </div>
            
            <div className="space-y-8 max-w-4xl mx-auto">
              {positions.map((position, index) => (
                <Card key={index} className="shadow-sm hover:shadow-lg transition-all duration-300">
                  <CardHeader>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <div>
                        <CardTitle className="text-xl mb-2">{position.title}</CardTitle>
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="secondary" className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {position.location}
                          </Badge>
                          <Badge variant="outline" className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {position.type}
                          </Badge>
                          <Badge className="bg-savvy-blue/10 text-savvy-blue">
                            {position.department}
                          </Badge>
                        </div>
                      </div>
                      <Button className="bg-savvy-gold text-savvy-dark hover:bg-savvy-gold/90">
                        <Mail className="h-4 w-4 mr-2" />
                        Apply Now
                      </Button>
                    </div>
                  </CardHeader>
                  
                  <CardContent className="space-y-6">
                    <p className="text-muted-foreground leading-relaxed">
                      {position.description}
                    </p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-semibold mb-3">Requirements</h4>
                        <ul className="space-y-2">
                          {position.requirements.map((req, reqIndex) => (
                            <li key={reqIndex} className="text-sm text-muted-foreground flex items-start">
                              <span className="text-savvy-blue mr-2 mt-1">•</span>
                              {req}
                            </li>
                          ))}
                        </ul>
                      </div>
                      
                      <div>
                        <h4 className="font-semibold mb-3">Responsibilities</h4>
                        <ul className="space-y-2">
                          {position.responsibilities.map((resp, respIndex) => (
                            <li key={respIndex} className="text-sm text-muted-foreground flex items-start">
                              <span className="text-savvy-gold mr-2 mt-1">•</span>
                              {resp}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    
                    <div className="pt-4 border-t">
                      <p className="text-sm text-muted-foreground">
                        Apply: <a href={`mailto:${position.email}`} className="text-savvy-blue hover:underline">{position.email}</a>
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Benefits */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Why Work With Us?</h2>
              <p className="text-muted-foreground">
                We believe in taking care of our team so they can do their best work.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
              {benefits.map((benefit, index) => (
                <Card key={index} className="text-center shadow-sm hover:shadow-lg transition-all duration-300">
                  <CardHeader>
                    <div className="w-12 h-12 bg-gradient-to-br from-savvy-blue/20 to-savvy-gold/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      {benefit.icon}
                    </div>
                    <CardTitle className="text-lg">{benefit.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground text-sm">{benefit.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Company Values */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Our Values</h2>
              <p className="text-muted-foreground">
                The principles that guide how we work together and serve our customers.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl mx-auto">
              {values.map((value, index) => (
                <div key={index} className="flex items-center gap-3 p-4 bg-card rounded-lg border">
                  <div className="w-2 h-2 bg-savvy-gold rounded-full flex-shrink-0" />
                  <span className="text-sm">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Application Process */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold mb-4">Ready to Apply?</h2>
              <p className="text-gray-300 mb-8">
                Don't see a perfect match? We're always interested in hearing from talented individuals who are passionate about data analytics and transparency.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button className="bg-savvy-gold text-savvy-dark hover:bg-savvy-gold/90">
                  <Mail className="h-4 w-4 mr-2" />
                  Send Us Your Resume
                </Button>
                <Button variant="outline" className="border-white text-white hover:bg-white/10">
                  Learn More About Us
                </Button>
              </div>
              <p className="text-sm text-gray-400 mt-6">
                We're an equal opportunity employer committed to diversity and inclusion.
              </p>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Careers;