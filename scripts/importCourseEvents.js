import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import pool from './config/db.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const importCourseEvents = async () => {
    try {
        const filePath = path.join(__dirname, '../data/hemvarn_course_events.json');
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        const events = data.events;

        console.log(`Starting import of ${events.length} course events...`);

        // Get existing template IDs to ensure referential integrity
        const templateResult = await pool.query('SELECT id FROM course_templates');
        const validTemplateIds = new Set(templateResult.rows.map(row => row.id));

        for (const event of events) {
            const {
                id, templateId, courseDates, location, eventResponsible,
                applicationDeadline, spots, status, notes,
                lastModifiedBy, lastModified, sourceFiles
            } = event;

            if (!validTemplateIds.has(templateId)) {
                console.warn(`Warning: Template ID ${templateId} not found in database for event ${id}. Skipping or handle as needed.`);
                // You might want to skip or handle this differently depending on requirements
                // For now, let's skip to maintain FK integrity
                continue;
            }

            const queryText = `
                INSERT INTO course_events (
                    id, template_id, course_dates, location, event_responsible,
                    application_deadline, spots, status, notes,
                    last_modified_by, last_modified, source_files
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (id) DO UPDATE SET
                    template_id = EXCLUDED.template_id,
                    course_dates = EXCLUDED.course_dates,
                    location = EXCLUDED.location,
                    event_responsible = EXCLUDED.event_responsible,
                    application_deadline = EXCLUDED.application_deadline,
                    spots = EXCLUDED.spots,
                    status = EXCLUDED.status,
                    notes = EXCLUDED.notes,
                    last_modified_by = EXCLUDED.last_modified_by,
                    last_modified = EXCLUDED.last_modified,
                    source_files = EXCLUDED.source_files;
            `;

            const values = [
                id, templateId,
                JSON.stringify(courseDates || []),
                location, eventResponsible,
                applicationDeadline,
                spots, status, notes,
                lastModifiedBy, lastModified,
                JSON.stringify(sourceFiles || [])
            ];

            await pool.query(queryText, values);
            console.log(`Imported/Updated event: ${id}`);
        }

        console.log('Course events import completed successfully.');
    } catch (error) {
        console.error('Error importing course events:', error);
    } finally {
        await pool.end();
    }
};

importCourseEvents();
