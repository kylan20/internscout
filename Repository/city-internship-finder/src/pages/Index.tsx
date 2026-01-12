import { useState } from "react";
import { Shield, Zap, Filter, Briefcase, ExternalLink, Building2 } from "lucide-react";
import SearchBar from "@/components/SearchBar";
import FeatureCard from "@/components/FeatureCard";
import FloatingOrb from "@/components/FloatingOrb";

const Index = () => {
  const [companies, setCompanies] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async (city: string, industry: string) => {
    const API_URL = "https://internscout-backend.onrender.com";
    
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ 
        city: city,
        domains: industry ? industry.split(',').map(i => i.trim()) : ["software", "web development"],
        intents: ["company", "agency"]
      }),
    });

    if (!response.ok) {
      throw new Error("Search failed");
    }

    
    if (!response.body) throw new Error("No response body");

    //allow frontend to read chunks of data AS they arrive

    //create a reader
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    //loop while data is flowing
    while (true) {
      const {done, value} = await reader.read();

      if (done) break;

      //decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });

      //split by newlines (each line is one company)
      const lines = buffer.split("\n");

      //keep the last piece in buffer (in case it's cut off)
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.trim()) {
          try {
            const newCompany = JSON.parse(line);
            //add to existing list immediately
            setCompanies((prev) => [...prev, newCompany]);
          } catch (e) {
            console.error("Error parsing JSON line", e);
          }
        }
      }
    }


    setIsLoading(false);
  };

  const features = [
    {
      icon: Filter,
      title: "Smart Filtering",
      description: "Automatically excludes social media posts, listicles, and generic job boards for quality results.",
    },
    {
      icon: Zap,
      title: "Real-Time Results",
      description: "Fresh internship opportunities scraped directly from company websites and trusted sources.",
    },
    {
      icon: Shield,
      title: "No Spam",
      description: "Skip the noise. Filter's out duplicate postings and aggregator spam automatically.",
    },
    {
      icon: Briefcase,
      title: "Direct Applications",
      description: "Links go straight to the source—apply directly on company career pages.",
    },
  ];

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background orbs */}
      <FloatingOrb size="lg" className="top-0 -right-48 animate-float" />
      <FloatingOrb size="md" className="bottom-32 -left-32 animate-float-delayed" />
      <FloatingOrb size="sm" className="top-1/3 left-1/4 animate-float" />

      <div className="relative z-10">
        {/* Hero Section */}
        <section className="container mx-auto px-4 pt-20 pb-16 md:pt-32 md:pb-24">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card text-sm text-muted-foreground mb-8">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              Powered by smart scraping
            </div>

            {/* Headline */}
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
              Find internships
              <br />
              <span className="text-gradient">without the noise</span>
            </h1>

            {/* Subheadline */}
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-12">
              Search any city and discover real internship opportunities. 
              No listicles, no social media spam—just direct links to apply.
            </p>

            {/* Search Bar */}
            <SearchBar onSearch={handleSearch} />

            {/* Subtle hint */}
            <p className="text-sm text-muted-foreground/60 mt-6">
              Try: Boston, Austin, Seattle, or any city you'd like to work in
            </p>
          </div>
        </section>

        {/* Results Section */}
        {companies.length > 0 && (
          <section className="container mx-auto px-4 py-8">
            <h2 className="text-2xl font-bold mb-6 text-center">
              Found {companies.length} Companies
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
              {companies.map((company: any, i: number) => (
                <div
                  key={i}
                  className="glass-card glow-border rounded-xl p-6 transition-all duration-300 hover:scale-[1.02]"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center">
                      <Building2 className="w-6 h-6 text-primary" />
                    </div>
                    <span className="text-xs px-2 py-1 rounded-full bg-primary/20 text-primary">
                      {company.Type}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold mb-3">{company["Company Name"]}</h3>
                  <a
                    href={company.Link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
                  >
                    Visit Career Page <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Features Section */}
        <section className="container mx-auto px-4 py-16 md:py-24">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">
              Why use InternScout?
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              InternScout was created because job boards are full of garbage. Here's what makes this different.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
            {features.map((feature, index) => (
              <FeatureCard
                key={index}
                icon={feature.icon}
                title={feature.title}
                description={feature.description}
              />
            ))}
          </div>
        </section>

        {/* Footer */}
        <footer className="container mx-auto px-4 py-8 border-t border-border/50">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
            <p>Built for students, by a student</p>
            <p>© 2026 InternScout. Find your next opportunity.</p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Index;