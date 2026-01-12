import { useState } from "react";
import { Search, Loader2, MapPin, Briefcase } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface SearchBarProps {
  onSearch: (city: string, industry: string) => Promise<void>;
}

const SearchBar = ({ onSearch }: SearchBarProps) => {
  const [city, setCity] = useState("");
  const [industry, setIndustry] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const trimmedCity = city.trim();
    const trimmedIndustry = industry.trim();
    
    if (!trimmedCity) {
      toast({
        title: "Please enter a city",
        description: "Enter a city name to search for internships.",
        variant: "destructive",
      });
      return;
    }

    if (trimmedCity.length > 100 || trimmedIndustry.length > 100) {
      toast({
        title: "Input too long",
        description: "Please enter shorter values.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      await onSearch(trimmedCity, trimmedIndustry);
      toast({
        title: "Search submitted!",
        description: `Searching for ${trimmedIndustry || "all"} internships in ${trimmedCity}...`,
      });
    } catch (error) {
      toast({
        title: "Something went wrong",
        description: "Failed to search. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-4xl mx-auto">
      <div className="glass-card glow-border rounded-2xl p-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 transition-all duration-300 hover:shadow-[var(--shadow-glow)]">
        <div className="flex items-center gap-3 flex-1 pl-4">
          <MapPin className="w-5 h-5 text-muted-foreground flex-shrink-0" />
          <Input
            type="text"
            placeholder="City (e.g., Albany, NY)"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="border-0 bg-transparent text-foreground placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:ring-offset-0 text-lg"
            disabled={isLoading}
            maxLength={100}
          />
        </div>
        <div className="hidden sm:block w-px h-8 bg-border/50" />
        <div className="flex items-center gap-3 flex-1 pl-4 sm:pl-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-3 w-full">
                  <Briefcase className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                  <Input
                    type="text"
                    placeholder="Industry (e.g., Software, Civil Engineering)"
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="border-0 bg-transparent text-foreground placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:ring-offset-0 text-lg w-full"
                    disabled={isLoading}
                    maxLength={100}
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Tip: You can search multiple industries by separating them with commas!</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <Button
          type="submit"
          disabled={isLoading}
          className="h-12 px-6 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 font-semibold text-base transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              <Search className="w-5 h-5 mr-2" />
              Search
            </>
          )}
        </Button>
      </div>
    </form>
  );
};

export default SearchBar;
