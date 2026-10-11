import { Sparkles } from "lucide-react";

interface Props {
  items: string[];
  onPick: (text: string) => void;
}

export default function SuggestChips({ items, onPick }: Props) {
  if (!items.length) return null;
  return (
    <div className="flex flex-wrap gap-2 pl-11">
      <Sparkles size={14} className="mt-1.5 text-brand-purple" />
      {items.map((it, i) => (
        <button
          key={i}
          onClick={() => onPick(it)}
          className="rounded-full border border-ink-600 bg-ink-800 px-3 py-1.5 text-[12.5px] text-txt-mid transition duration-150 hover:border-brand-teal hover:bg-brand-teal/10 hover:text-brand-teal"
        >
          {it}
        </button>
      ))}
    </div>
  );
}
