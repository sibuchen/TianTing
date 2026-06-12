import { FluidDropdown } from "@/components/ui/fluid-dropdown";
import { Languages, Globe } from "lucide-react";
import React from "react";

export default function DemoOne() {
  const [value, setValue] = React.useState("zh");
  
  return (
    <div className="p-10 max-w-md mx-auto">
      <FluidDropdown 
        value={value}
        onChange={setValue}
        options={[
          { id: 'zh', label: '中文 (简体)', icon: Languages, color: '#FF6B6B' },
          { id: 'en', label: 'English', icon: Globe, color: '#45B7D1' },
        ]}
      />
    </div>
  );
}
