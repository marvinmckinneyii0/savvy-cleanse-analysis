import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { Mail, MapPin, Clock, Phone, Send, MessageSquare, HelpCircle, Briefcase } from 'lucide-react';

const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle form submission here
    console.log('Form submitted:', formData);
    // Reset form
    setFormData({
      name: '',
      email: '',
      subject: '',
      message: ''
    });
  };

  const contactInfo = [
    {
      icon: <Mail className="h-6 w-6 text-savvy-blue" />,
      title: "Email Us",
      content: "support@savvyanalytics.info",
      description: "Get in touch for general inquiries and support"
    },
    {
      icon: <MapPin className="h-6 w-6 text-savvy-gold" />,
      title: "Location",
      content: "Lisbon, Portugal",
      description: "Our headquarters (Remote-first company)"
    },
    {
      icon: <Clock className="h-6 w-6 text-savvy-blue" />,
      title: "Response Time",
      content: "Within 24 hours",
      description: "We typically respond to all inquiries quickly"
    }
  ];

  const contactTypes = [
    {
      icon: <MessageSquare className="h-8 w-8 text-savvy-blue" />,
      title: "General Support",
      description: "Questions about using SavvyClean, troubleshooting, or account issues",
      email: "support@savvyanalytics.info"
    },
    {
      icon: <Briefcase className="h-8 w-8 text-savvy-gold" />,
      title: "Business Inquiries",
      description: "Enterprise sales, partnerships, and custom solutions",
      email: "business@savvyanalytics.info"
    },
    {
      icon: <HelpCircle className="h-8 w-8 text-savvy-blue" />,
      title: "Technical Questions",
      description: "API documentation, integration help, and developer support",
      email: "developers@savvyanalytics.info"
    }
  ];

  const faqs = [
    {
      question: "How quickly can I get started with SavvyClean?",
      answer: "You can start using SavvyClean immediately after signing up. Simply upload your data and begin cleaning and analyzing within minutes."
    },
    {
      question: "What file formats do you support?",
      answer: "We support CSV, Excel (.xlsx, .xls), JSON, and TSV files. We're continuously adding support for more formats based on user feedback."
    },
    {
      question: "Is my data secure?",
      answer: "Yes, we take data security seriously. All data is encrypted in transit and at rest, and we follow industry-standard security practices."
    },
    {
      question: "Can I export my cleaned data?",
      answer: "Absolutely! You can export your cleaned data in multiple formats including CSV, Excel, and as Python/Jupyter notebooks for further analysis."
    }
  ];

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-4xl mx-auto">
              <Mail className="h-16 w-16 text-savvy-gold mx-auto mb-6" />
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                Get in
                <span className="text-savvy-gold"> Touch</span>
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                Have questions about SavvyClean? Need help with your data analytics workflow? We're here to help.
              </p>
            </div>
          </div>
        </section>

        {/* Contact Info Cards */}
        <section className="py-12 bg-white dark:bg-savvy-dark border-b">
          <div className="container px-4 md:px-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {contactInfo.map((info, index) => (
                <Card key={index} className="text-center shadow-sm">
                  <CardContent className="p-6">
                    <div className="w-12 h-12 bg-gradient-to-br from-savvy-blue/20 to-savvy-gold/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      {info.icon}
                    </div>
                    <h3 className="font-semibold mb-2">{info.title}</h3>
                    <p className="text-lg font-medium mb-1">{info.content}</p>
                    <p className="text-sm text-muted-foreground">{info.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Contact Form and Types */}
        <section className="py-16 bg-gradient-to-r from-savvy-blue/5 to-savvy-gold/5">
          <div className="container px-4 md:px-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 max-w-6xl mx-auto">
              {/* Contact Form */}
              <div>
                <h2 className="text-3xl font-bold mb-6">Send Us a Message</h2>
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Contact Form</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-6">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="name">Name</Label>
                          <Input
                            id="name"
                            name="name"
                            value={formData.name}
                            onChange={handleInputChange}
                            required
                            placeholder="Your full name"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="email">Email</Label>
                          <Input
                            id="email"
                            name="email"
                            type="email"
                            value={formData.email}
                            onChange={handleInputChange}
                            required
                            placeholder="your@email.com"
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="subject">Subject</Label>
                        <Input
                          id="subject"
                          name="subject"
                          value={formData.subject}
                          onChange={handleInputChange}
                          required
                          placeholder="What's this about?"
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="message">Message</Label>
                        <Textarea
                          id="message"
                          name="message"
                          value={formData.message}
                          onChange={handleInputChange}
                          required
                          rows={6}
                          placeholder="Tell us how we can help you..."
                        />
                      </div>
                      
                      <Button type="submit" className="w-full bg-savvy-blue hover:bg-savvy-blue/90">
                        <Send className="h-4 w-4 mr-2" />
                        Send Message
                      </Button>
                    </form>
                  </CardContent>
                </Card>
              </div>

              {/* Contact Types */}
              <div>
                <h2 className="text-3xl font-bold mb-6">How Can We Help?</h2>
                <div className="space-y-6">
                  {contactTypes.map((type, index) => (
                    <Card key={index} className="shadow-sm hover:shadow-lg transition-all duration-300">
                      <CardContent className="p-6">
                        <div className="flex items-start gap-4">
                          <div className="w-16 h-16 bg-gradient-to-br from-savvy-blue/20 to-savvy-gold/20 rounded-lg flex items-center justify-center flex-shrink-0">
                            {type.icon}
                          </div>
                          <div className="flex-grow">
                            <h3 className="font-semibold mb-2">{type.title}</h3>
                            <p className="text-muted-foreground mb-3 text-sm leading-relaxed">
                              {type.description}
                            </p>
                            <a
                              href={`mailto:${type.email}`}
                              className="text-savvy-blue hover:text-savvy-blue/80 text-sm font-medium"
                            >
                              {type.email}
                            </a>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Frequently Asked Questions</h2>
              <p className="text-muted-foreground">
                Quick answers to common questions. Can't find what you're looking for? Contact us directly.
              </p>
            </div>
            
            <div className="max-w-3xl mx-auto space-y-6">
              {faqs.map((faq, index) => (
                <Card key={index} className="shadow-sm">
                  <CardContent className="p-6">
                    <h3 className="font-semibold mb-3">{faq.question}</h3>
                    <p className="text-muted-foreground leading-relaxed">{faq.answer}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 bg-gradient-to-br from-savvy-dark via-savvy-midnight to-savvy-slate text-white">
          <div className="container px-4 md:px-6">
            <div className="text-center max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold mb-4">Still Have Questions?</h2>
              <p className="text-gray-300 mb-8">
                Our team is here to help you succeed with SavvyClean. Don't hesitate to reach out.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button className="bg-savvy-gold text-savvy-dark hover:bg-savvy-gold/90">
                  <Mail className="h-4 w-4 mr-2" />
                  Email Support
                </Button>
                <Button variant="outline" className="border-white text-white hover:bg-white/10">
                  Browse Documentation
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

export default Contact;