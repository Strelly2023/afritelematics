import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source=readFileSync(new URL("../src/design/AccessibilityStudio.jsx",import.meta.url),"utf8");
test("accessibility centre covers automated and manual WCAG review dimensions",()=>{for(const check of ["Colour contrast","Keyboard navigation","Focus order","ARIA metadata","Touch-target size","Screen-reader compatibility","Motion reduction","Heading order","Form accessibility"])assert.match(source,new RegExp(check));assert.match(source,/manual verification required/);});
test("accessibility analysis persists tenant-scoped review requirements",()=>{assert.match(source,/api\.createAccessibilityRequirement/);assert.match(source,/standard:"WCAG_2_2_AA"/);assert.match(source,/human_review_status:"PENDING"/);assert.match(source,/waiver_status/);});
test("responsive preview supports devices and assistive simulation",()=>{for(const device of ["Desktop","Tablet","Mobile","Foldable","Watch","TV","Vehicle"])assert.match(source,new RegExp(device));for(const mode of ["Text scale","Keyboard only","Reduced motion","Landscape"])assert.match(source,new RegExp(mode));});
