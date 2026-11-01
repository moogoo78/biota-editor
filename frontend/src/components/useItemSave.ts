import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { Item, Publication } from "../api/types";

/** Mutation that returns a fresh Item: refresh the item cache, the name list counts and the preview. */
export function useItemSave<V>(itemId: number, pubId: number, fn: (v: V) => Promise<Item>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: (it) => {
      qc.setQueryData(["item", itemId], it);
      qc.setQueryData<Publication>(["publication", pubId], (p) => p && {
        ...p,
        items: p.items.map((x) => x.id === it.id
          ? { ...x, n_specimens: it.specimens.length, n_images: it.images.length, common_names: it.common_names }
          : x),
      });
      qc.invalidateQueries({ queryKey: ["preview", pubId] });
    },
  });
}
