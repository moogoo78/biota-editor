import type { ReactNode } from "react";
import {
  DndContext, KeyboardSensor, PointerSensor, closestCenter, useSensor, useSensors, type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext, arrayMove, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy,
  rectSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useTranslation } from "react-i18next";

export function SortableList<T>({ items, getId, onChange, render, grid = false, className }: {
  items: T[];
  getId: (x: T) => string;
  onChange: (next: T[]) => void;
  render: (x: T, index: number, handle: ReactNode) => ReactNode;
  grid?: boolean;
  className?: string;
}) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );
  const ids = items.map(getId);
  const onDragEnd = (e: DragEndEvent) => {
    if (!e.over || e.active.id === e.over.id) return;
    onChange(arrayMove(items, ids.indexOf(String(e.active.id)), ids.indexOf(String(e.over.id))));
  };
  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
      <SortableContext items={ids} strategy={grid ? rectSortingStrategy : verticalListSortingStrategy}>
        <div className={className}>
          {items.map((x, i) => (
            <Row key={ids[i]} id={ids[i]}>{(handle) => render(x, i, handle)}</Row>
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}

function Row({ id, children }: { id: string; children: (handle: ReactNode) => ReactNode }) {
  const { t } = useTranslation();
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id });
  const style = { transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.6 : 1 };
  const handle = (
    <button type="button" className="handle" title={t("common.drag")} aria-label={t("common.drag")}
      {...attributes} {...listeners}>⋮⋮</button>
  );
  return <div ref={setNodeRef} style={style}>{children(handle)}</div>;
}
