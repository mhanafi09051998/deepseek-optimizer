# dependency-cache

A small cache where entries can declare dependencies on other entries.

When a key is invalidated, every entry that depends on it must be invalidated
too, transitively. Expiry has the same consequence as explicit invalidation.
