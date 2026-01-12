interface FloatingOrbProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

const FloatingOrb = ({ className = "", size = "md" }: FloatingOrbProps) => {
  const sizeClasses = {
    sm: "w-32 h-32",
    md: "w-64 h-64",
    lg: "w-96 h-96",
  };

  return (
    <div
      className={`absolute rounded-full bg-primary/10 blur-3xl animate-pulse-glow pointer-events-none ${sizeClasses[size]} ${className}`}
    />
  );
};

export default FloatingOrb;
