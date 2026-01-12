import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const analyzeJson = () => {
    const filePath = path.join(__dirname, '../data/hemvarn_course_events.json');
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const events = data.events;

    console.log(`Total events in JSON: ${events.length}`);

    const ids = new Set();
    const duplicates = [];
    const missingTemplateId = [];
    const today = '20260109';
    let pastEvents = 0;

    events.forEach((e, index) => {
        if (!e.id) {
            console.log(`Event at index ${index} missing ID`);
        } else if (ids.has(e.id)) {
            duplicates.push(e.id);
        } else {
            ids.add(e.id);
        }

        if (!e.templateId) {
            missingTemplateId.push(e.id || index);
        }

        const startDate = e.courseDates && e.courseDates[0] ? e.courseDates[0].start : null;
        if (startDate && startDate < today) {
            pastEvents++;
        }
    });

    console.log(`Unique IDs: ${ids.size}`);
    console.log(`Events starting before ${today}: ${pastEvents}`);
    if (duplicates.length > 0) {
        console.log(`Duplicates: ${duplicates.join(', ')}`);
    }
    if (missingTemplateId.length > 0) {
        console.log(`Missing templateId: ${missingTemplateId.length}`);
    }
};

analyzeJson();
