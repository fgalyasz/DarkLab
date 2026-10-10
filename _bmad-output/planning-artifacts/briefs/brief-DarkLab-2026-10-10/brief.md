---
title: DarkLab
status: final
created: 2026-10-10
updated: 2026-10-10
---

# Product Brief: DarkLab

## Executive Summary

DarkLab is a free, open-source desktop application for the photographer who already works the Lightroom Classic way: import a shoot, cull it, develop the selects, and hand off files, prints, or a gallery. The product promise is workflow parity with Classic's seven modules. It is not a promise to open an Adobe catalog or to match Adobe's color science pixel for pixel.

The first public milestone is one real shoot. A photographer can import mixed RAW and JPEG, rate and filter the set, apply basic non-destructive tone and crop, and export JPEGs while the original files stay byte-for-byte unchanged.

## The Problem

Classic is the mental model a large share of working photographers already have, and it is a subscription. The open-source alternatives that exist are capable and different. darktable, RawTherapee, and digiKam ask the photographer to learn another catalog, another panel order, and another vocabulary. That switch is the cost, not the lack of a slider.

A photographer finishing a wedding wants the same sequence they already trust: copy the card in, reject the misses, correct the keepers, export for the client. They also want the files on their own disk, with no account standing between them and the originals.

## The Solution

DarkLab is a local catalog application with the Classic module bar: Library, Develop, Map, Book, Slideshow, Print, and Web. Import is a dialog, as it is in Classic. Develop settings are instructions stored beside the catalog and in an XMP sidecar. Export renders a new file. The original is never the save target.

The full module set is the product. The first release is the path through Library and Develop that finishes a shoot.

## What Makes This Different

The difference is familiarity, not a new editing idea. DarkLab keeps Classic's job order and module names so a photographer can find the work without a new theory of the catalog.

There is no technical moat. darktable will remain the stronger raw engine for some cameras, and Adobe will remain the reference renderer for anyone who needs Adobe profiles. DarkLab's bet is that an open, local, Classic-shaped workflow is a product people can adopt without first abandoning how they think. Execution is the advantage. Claiming otherwise would be false.

## Who This Serves

Anna is a solo wedding and portrait photographer. She shoots to a card, edits on a laptop, and delivers JPEGs. She knows Classic and does not want a subscription or a cloud library as the price of that knowledge.

Secondary: the hobby photographer with the same module habits and a smaller volume. Not served in the first release: studios that need simultaneous multi-user catalogs, tethered capture on set, or a mobile client.

## Success Criteria

A scripted shoot of about 200 mixed RAW and JPEG files completes import, cull, basic develop, and export with original hashes unchanged. Reopening the catalog restores the same develop settings. Five photographers who know Classic can point at the module for culling, developing, and printing without a tour.

The project does not treat a smaller color difference versus Lightroom as a release gate.

## Scope

In the first milestone: one catalog, import (add, copy, move) with a pre-commit count, duplicate handling, folders, grid, loupe, ratings, flags, color labels, basic filters, crop, white balance, basic tone, history, histogram, JPEG export, catalog backup.

Out of the first milestone, and still in the product: collections, keywords, metadata editing, the rest of Develop (curve, HSL, masks, healing, presets), Map, Book, Slideshow, Print, Web, and people tags.

Out of the product promise: Adobe catalog files, Adobe profiles, cloud sync, tethered capture, Adobe plugins, and Blurb ordering.

## Vision

If this works, DarkLab becomes the open desktop a Classic photographer can recommend without apologizing for a different workflow. Two to three years out, the seven modules are real, develop covers the Classic panel set including masks, and the catalog is still a file the photographer can copy to another disk.
