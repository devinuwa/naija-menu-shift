// Generated protein photos, embedded as data URIs. The photos live in
// per-protein modules under lib/protein-image-data/ so each file stays
// small enough to push and verify on its own; the soy-chunks photo is
// split across two modules that are joined here.
import awara from "./protein-image-data/awara";
import bambara from "./protein-image-data/bambara";
import dawadawa from "./protein-image-data/dawadawa";
import egusi from "./protein-image-data/egusi";
import mushrooms from "./protein-image-data/mushrooms";
import seitan from "./protein-image-data/seitan";
import soyMilk from "./protein-image-data/soy_milk";
import soyChunksA from "./protein-image-data/soy_chunks_a";
import soyChunksB from "./protein-image-data/soy_chunks_b";

export const PROTEIN_IMAGES: Record<string, string> = {
  awara,
  bambara,
  dawadawa,
  egusi,
  mushrooms,
  seitan,
  soy_chunks: soyChunksA + soyChunksB,
  soy_milk: soyMilk,
};
