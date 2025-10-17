import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default:
          "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
        secondary:
          "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
        success:
          "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
        warning:
          "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
        danger:
          "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
        outline:
          "border border-gray-300 text-gray-700 dark:border-gray-700 dark:text-gray-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
