import { EmptyState } from "@/components/States";

interface Props {
  title: string;
  phase: string;
}

export function PlaceholderPage({ title, phase }: Props): JSX.Element {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <div className="text-2xs font-medium uppercase tracking-wide text-fg-subtle">
          AlphaDesk
        </div>
        <h1 className="text-xl font-semibold tracking-tight text-fg">{title}</h1>
      </div>
      <EmptyState
        title={`Lands in ${phase}`}
        description="The design-system primitives it will use are already live under /design."
      />
    </div>
  );
}
