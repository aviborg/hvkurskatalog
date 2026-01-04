#!/usr/bin/env node
/**
* PDF Course Catalog Extraction Script
* 
* Extracts course information from PDF catalogs using GPT-4o vision API
* and outputs structured JSON for courseTemplates.json and courseEvents.json
*/

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { readdir } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { pdf } from 'pdf-to-img';
import OpenAI from 'openai';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT_DIR = join(__dirname, '..');

const PDF_DIR = join(ROOT_DIR, 'public', 'kurskataloger');
const DATA_DIR = join(ROOT_DIR, 'data');
const TEMPLATES_FILE = join(DATA_DIR, 'courseTemplates.json');
const EVENTS_FILE = join(DATA_DIR, 'courseEvents.json');

const DRY_RUN = process.argv.includes('--dry-run');

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// JSON schemas for structured output
const COURSE_TEMPLATE_SCHEMA = {
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique identifier for the course template, lowercase with hyphens, without the word 'kurs' (e.g., 'gruppchef-1', 'tccc-cls')."
    },
    "name": {
      "type": "string",
      "description": "Full course name in Swedish, verbatim, without the word 'kurs'."
    },
    "shortName": {
      "type": "string",
      "description": "Short established name or abbreviation (normally 2 letters + number, but longer accepted if established, e.g., 'KombU', 'GC12', 'TCCCCLS', 'GKÖLAK')."
    },
    "category": {
      "type": "string",
      "description": "Course category (e.g., 'Chefsutbildningar', 'Funktionsutbildningar')."
    },
    "courseCode": {
      "type": ["string", "null"],
      "description": "Official course code if available."
    },
    "description": {
      "type": "string",
      "description": "Verbatim course description."
    },
    "targetAudience": {
      "type": "string",
      "description": "Who the course is intended for, verbatim."
    },
    "syllabus": {
      "type": "string",
      "description": "Course syllabus or content overview."
    },
    "purpose": {
      "type": "string",
      "description": "Purpose of the course, verbatim where possible."
    },
    "learningObjectives": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of learning objectives."
    },
    "primaryLearningObjective": {
      "type": "string",
      "description": "Primary learning objective after completing the course."
    },
    "secondaryLearningObjectives": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Secondary learning objectives."
    },
    "examination": {
      "type": "string",
      "description": "How the course is examined."
    },
    "prerequisites": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Prerequisites for the course."
    },
    "literature": {
      "type": "string",
      "description": "Required literature or course material."
    },
    "additionalInfo": {
      "type": ["string", "null"],
      "description": "Additional information or remarks."
    },
    "typicalDuration": {
      "type": "number",
      "description": "Typical duration in days."
    },
    "courseResponsible": {
      "type": "string",
      "description": "Responsible organization (no spaces, e.g., 'HvSS', 'MRM', 'MRV')."
    },
    "baseTemplateIds": {
      "type": "array",
      "items": { "type": "string" },
      "description": "IDs of base course templates covered by this template (used for merged or derived courses)."
    },
    "sourceFiles": {
      "type": "array",
      "items": { "type": "string" },
      "description": "PDF or other sources from which this template was extracted."
    }
  },
  "required": [
    "id",
    "name",
    "shortName",
    "category",
    "courseCode",
    "description",
    "targetAudience",
    "syllabus",
    "purpose",
    "learningObjectives",
    "primaryLearningObjective",
    "secondaryLearningObjectives",
    "examination",
    "prerequisites",
    "literature",
    "additionalInfo",
    "typicalDuration",
    "courseResponsible",
    "baseTemplateIds",
    "sourceFiles"
  ],
  "additionalProperties": false
};

const COURSE_EVENT_SCHEMA = {
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique event identifier (e.g., 'evt-gruppchef-12-mrm-summer-2026')."
    },
    "templateId": {
      "type": "string",
      "description": "Reference to the primary course template ID."
    },
    "coveredTemplateIds": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of course template IDs whose learning outcomes are covered by this event."
    },
    "courseDates": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "start": {
            "type": "string",
            "description": "Start date in YYYYMMDD format."
          },
          "end": {
            "type": "string",
            "description": "End date in YYYYMMDD format."
          }
        },
        "required": ["start", "end"],
        "additionalProperties": false
      },
      "description": "One or more course date periods."
    },
    "location": {
      "type": "string",
      "description": "Location where the course is held."
    },
    "courseResponsible": {
      "type": "string",
      "description": "Responsible organization for this event (no spaces)."
    },
    "applicationDeadline": {
      "type": "string",
      "description": "Application deadline in YYYYMMDD format."
    },
    "spots": {
      "type": "number",
      "description": "Number of available spots."
    },
    "status": {
      "type": "string",
      "enum": ["open", "closed", "cancelled"],
      "description": "Course event status."
    },
    "notes": {
      "type": "string",
      "description": "Additional notes about this specific event."
    },
    "sourceFiles": {
      "type": "array",
      "items": { "type": "string" },
      "description": "PDF or other sources from which this event was extracted."
    }
  },
  "required": [
    "id",
    "templateId",
    "coveredTemplateIds",
    "courseDates",
    "location",
    "courseResponsible",
    "applicationDeadline",
    "spots",
    "status",
    "notes",
    "sourceFiles"
  ],
  "additionalProperties": false
};

/**
* Convert PDF pages to base64-encoded images
*/
async function pdfToImages(pdfPath) {
  console.log(`  Converting PDF to images: ${pdfPath}`);
  const images = [];
  
  try {
    const document = await pdf(pdfPath, { scale: 2 });
    let pageNum = 0;
    
    for await (const image of document) {
      pageNum++;
      const base64 = image.toString('base64');
      images.push({
        page: pageNum,
        base64,
        mediaType: 'image/png'
      });
    }
    
    console.log(`  Converted ${images.length} pages`);
  } catch (error) {
    console.error(`  Error converting PDF: ${error.message}`);
  }
  
  return images;
}

/**
* Extract course information from PDF images using GPT-4o
*/
async function extractCoursesFromImages(images, pdfName) {
  console.log(`  Sending ${images.length} pages to GPT-4o for extraction...`);
  
  // Build content array with all page images
  const content = [
    {
      type: "text",
      text: `You are extracting course catalog information from a Swedish military (Hemvärnet/Home Guard) training catalog PDF named "${pdfName}".
      
Extract ALL courses found in these pages. For each course, provide:
      
1. **Course Templates** (course definitions with description, objectives, prerequisites, etc.)
2. **Course Events** (specific scheduled instances with dates, locations, spots)
      
Output as JSON with two arrays:
{
  "templates": [...],  // Course template objects
  "events": [...]      // Course event objects
}
      
Important:
- Use Swedish text as-is, don't translate
- Dates should be in YYYYMMDD format
- Generate unique IDs: templates use lowercase with hyphens (e.g., "gu-f"), events use "evt-{templateId}-{courseResponsible}-{season/month}-{year}"
- If a field is not found in the PDF, use null or empty array as appropriate
- Extract as much detail as possible from the PDF content`
    }
  ];
  
  // Add images (limit to first 20 pages to stay within token limits)
  const pagesToProcess = images.slice(0, 20);
  for (const img of pagesToProcess) {
    content.push({
      type: "image_url",
      image_url: {
        url: `data:${img.mediaType};base64,${img.base64}`,
        detail: "high"
      }
    });
  }
  
  try {
    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "user",
          content
        }
      ],
      max_tokens: 16000,
      response_format: { type: "json_object" }
    });
    
    const result = JSON.parse(response.choices[0].message.content);
    console.log(`  Extracted ${result.templates?.length || 0} templates and ${result.events?.length || 0} events`);
    return result;
  } catch (error) {
    console.error(`  Error calling GPT-4o: ${error.message}`);
    return { templates: [], events: [] };
  }
}

/**
* Merge extracted data with existing data, avoiding duplicates
*/
function mergeData(existing, extracted, keyField = 'id') {
  const merged = [...existing];
  const existingIds = new Set(existing.map(item => item[keyField]));
  const existingCodes = new Set(existing.map(item => item.courseCode).filter(Boolean));
  
  for (const item of extracted) {
    // Check for duplicates by id or courseCode
    const isDuplicate = existingIds.has(item[keyField]) || 
    (item.courseCode && existingCodes.has(item.courseCode));
    
    if (isDuplicate) {
      // Update existing entry
      const index = merged.findIndex(e => 
        e[keyField] === item[keyField] || 
        (item.courseCode && e.courseCode === item.courseCode)
      );
      if (index !== -1) {
        merged[index] = { ...merged[index], ...item, lastModified: getCurrentDate() };
        console.log(`  Updated existing: ${item[keyField]}`);
      }
    } else {
      // Add new entry
      merged.push({
        ...item,
        createdBy: "ai-extraction",
        createdAt: getCurrentDate(),
        lastModified: getCurrentDate()
      });
      console.log(`  Added new: ${item[keyField]}`);
    }
  }
  
  return merged;
}

/**
* Get current date in YYYYMMDD format
*/
function getCurrentDate() {
  const now = new Date();
  return now.toISOString().slice(0, 10).replace(/-/g, '');
}

/**
* Load existing JSON file or return empty array
*/
function loadJson(filePath) {
  if (existsSync(filePath)) {
    return JSON.parse(readFileSync(filePath, 'utf-8'));
  }
  return [];
}

/**
* Save JSON file with pretty formatting
*/
function saveJson(filePath, data) {
  writeFileSync(filePath, JSON.stringify(data, null, 4) + '\n', 'utf-8');
}

/**
* Main extraction process
*/
async function main() {
  console.log('='.repeat(60));
  console.log('PDF Course Catalog Extraction');
  console.log('='.repeat(60));
  
  if (DRY_RUN) {
    console.log('🔍 DRY RUN MODE - No files will be modified\n');
  }
  
  if (!process.env.OPENAI_API_KEY) {
    console.error('Error: OPENAI_API_KEY environment variable is not set');
    process.exit(1);
  }
  
  // Get list of PDF files
  const files = await readdir(PDF_DIR);
  const pdfFiles = files.filter(f => f.toLowerCase().endsWith('.pdf'));
  
  console.log(`Found ${pdfFiles.length} PDF files to process:\n`);
  pdfFiles.forEach(f => console.log(`  - ${f}`));
  console.log();
  
  // Load existing data
  let templates = loadJson(TEMPLATES_FILE);
  let events = loadJson(EVENTS_FILE);
  
  console.log(`Existing data: ${templates.length} templates, ${events.length} events\n`);
  
  // Process each PDF
  for (const pdfFile of pdfFiles) {
    console.log(`\nProcessing: ${pdfFile}`);
    console.log('-'.repeat(50));
    
    const pdfPath = join(PDF_DIR, pdfFile);
    
    // Convert PDF to images
    const images = await pdfToImages(pdfPath);
    if (images.length === 0) {
      console.log('  Skipping: Could not convert PDF');
      continue;
    }
    
    // Extract courses using GPT-4o
    const extracted = await extractCoursesFromImages(images, pdfFile);
    
    // Merge with existing data
    if (extracted.templates?.length > 0) {
      templates = mergeData(templates, extracted.templates, 'id');
    }
    if (extracted.events?.length > 0) {
      events = mergeData(events, extracted.events, 'id');
    }
  }
  
  // Save results
  console.log('\n' + '='.repeat(60));
  console.log('Results');
  console.log('='.repeat(60));
  console.log(`Total templates: ${templates.length}`);
  console.log(`Total events: ${events.length}`);
  
  if (!DRY_RUN) {
    saveJson(TEMPLATES_FILE, templates);
    saveJson(EVENTS_FILE, events);
    console.log('\n✅ Data files updated successfully');
  } else {
    console.log('\n🔍 Dry run complete - no files modified');
    console.log('\nExtracted data preview:');
    console.log(JSON.stringify({ templates: templates.slice(-3), events: events.slice(-3) }, null, 2));
  }
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
