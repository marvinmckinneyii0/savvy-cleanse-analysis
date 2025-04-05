
import { Moon, Sun } from "lucide-react";
import { useTheme } from "./ThemeProvider";
import { Button } from "./ui/button";

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
      className="rounded-full border border-savvy-gold/20 bg-background"
      aria-label="Toggle theme"
    >
      {theme === "light" ? 
        <Moon className="h-5 w-5 text-savvy-gold" /> : 
        <Sun className="h-5 w-5 text-savvy-gold" />
      }
    </Button>
  );
}
