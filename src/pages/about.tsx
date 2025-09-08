import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { Target, Users, Lightbulb, Award, MapPin, Mail } from 'lucide-react';

const About = () => {
  const values = [
    {
      icon: <Target className="h-8 w-8 text-savvy-blue" />,
      title: "Transparency",
      description: "We believe in showing you exactly how your insights are generated. No black boxes, just clear methodology and statistical rigor."
    },
    {
      icon: <Users className="h-8 w-8 text-savvy-gold" />,
      title: "Accessibility",
      description: "Powerful analytics shouldn't require a PhD. We make sophisticated data science accessible to everyone."
    },
    {
      icon: <Lightbulb className="h-8 w-8 text-savvy-blue" />,
      title: "Intelligence",
      description: "We leverage cutting-edge AI and machine learning to automate the tedious parts of data analysis while maintaining human oversight."
    }
  ];

  const team = [
    {
      name: "Sarah Rodriguez",
      role: "CEO & Co-Founder",
      bio: "Former data science leader at Fortune 500 companies. PhD in Statistics from Stanford. Passionate about democratizing analytics.",
      initials: "SR"
    },
    {
      name: "Marcus Chen",
      role: "CTO & Co-Founder", 
      bio: "Ex-Google engineer with 10+ years in ML infrastructure. MIT Computer Science. Believes in building tools that scale.",
      initials: "MC"
    },
    {
      name: "Elena Vasquez",
      role: "Lead Engineer",
      bio: "Full-stack engineer specializing in data platforms. Former Netflix and Airbnb. Loves solving complex technical challenges.",
      initials: "EV"
    }
  ];

  const milestones = [
    {
      year: "2023",
      title: "Company Founded",
      description: "Started as a consultancy helping businesses adopt AI responsibly"
    },
    {
      year: "2024",
      title: "SavvyClean Launch",
      description: "Released our first product focusing on transparent data analytics"
    },
    {
      year: "2024",
      title: "10K+ Users",
      description: "Reached our first major user milestone with teams across 50+ countries"
    },
    {
      year: "2025",
      title: "API Release",
      description: "Launching developer tools and enterprise integrations"
    }
  ];

  return (
    <div className="flex flex-col min-h-screen" data-page="about">
      <Navbar />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-4xl mx-auto">
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                About
                <span className="text-savvy-gold"> SavvyClean</span>
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-8">
                We're on a mission to turn data chaos into clarity, one dataset at a time.
              </p>
              <div className="flex items-center justify-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4" />
                  Lisbon, Portugal
                </div>
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  support@savvyanalytics.info
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Mission Statement */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="text-3xl font-bold mb-8">Our Mission</h2>
              <p className="text-xl text-muted-foreground leading-relaxed mb-8">
                SavvyClean is built by <strong>Savvy Analytics</strong>, a consultancy dedicated to helping businesses adopt AI responsibly. We believe that powerful analytics should be transparent, accessible, and intelligent.
              </p>
              <div className="bg-gradient-to-r from-savvy-blue/10 to-savvy-gold/10 rounded-lg p-8">
                <blockquote className="text-2xl font-semibold text-center italic">
                  "Turn chaos into clarity, one dataset at a time."
                </blockquote>
                <p className="text-muted-foreground mt-4">— Our Company Motto</p>
              </div>
            </div>
          </div>
        </section>

        {/* Values */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Our Values</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                These core principles guide everything we build and every decision we make.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {values.map((value, index) => (
                <Card key={index} className="text-center shadow-sm hover:shadow-lg transition-all duration-300">
                  <CardHeader>
                    <div className="w-16 h-16 bg-gradient-to-br from-savvy-blue/20 to-savvy-gold/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      {value.icon}
                    </div>
                    <CardTitle className="text-xl">{value.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground leading-relaxed">{value.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Team */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Meet Our Team</h2>
              <p className="text-muted-foreground">
                The passionate individuals behind SavvyClean's mission to democratize data analytics.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {team.map((member, index) => (
                <Card key={index} className="text-center shadow-sm hover:shadow-lg transition-all duration-300">
                  <CardHeader>
                    <div className="w-20 h-20 bg-gradient-to-br from-savvy-blue to-savvy-gold rounded-full flex items-center justify-center mx-auto mb-4">
                      <span className="text-white text-xl font-bold">{member.initials}</span>
                    </div>
                    <CardTitle className="text-xl">{member.name}</CardTitle>
                    <Badge variant="secondary" className="mx-auto">
                      {member.role}
                    </Badge>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground leading-relaxed">{member.bio}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Timeline */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Our Journey</h2>
              <p className="text-muted-foreground">
                Key milestones in SavvyClean's evolution from idea to platform.
              </p>
            </div>
            
            <div className="max-w-3xl mx-auto">
              <div className="space-y-8">
                {milestones.map((milestone, index) => (
                  <div key={index} className="flex items-start gap-6">
                    <div className="flex-shrink-0 w-20 h-20 bg-white dark:bg-card rounded-full border-4 border-savvy-blue flex items-center justify-center shadow-lg">
                      <span className="text-savvy-blue font-bold text-sm">{milestone.year}</span>
                    </div>
                    <div className="flex-grow">
                      <h3 className="text-xl font-semibold mb-2">{milestone.title}</h3>
                      <p className="text-muted-foreground">{milestone.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
              {[
                { value: "10K+", label: "Active Users" },
                { value: "50+", label: "Countries" },
                { value: "500M+", label: "Rows Processed" },
                { value: "99.9%", label: "Uptime" }
              ].map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-3xl md:text-4xl font-bold text-savvy-blue mb-2">
                    {stat.value}
                  </div>
                  <div className="text-muted-foreground">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold mb-4">Join Our Mission</h2>
              <p className="text-gray-300 mb-8">
                Ready to transform how your organization approaches data analytics? Let's turn your data chaos into clarity.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button className="bg-savvy-gold text-savvy-dark hover:bg-savvy-gold/90">
                  Start Free Trial
                </Button>
                <Button variant="outline" className="border-white text-white hover:bg-white/10">
                  Contact Our Team
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

export default About;