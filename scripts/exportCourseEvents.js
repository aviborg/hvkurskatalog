import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import pool from './config/db.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const exportCourseEvents = async () => {
    try {
        console.log('Fetching course events from database...');

        const result = await pool.query('SELECT * FROM course_events ORDER BY id ASC');

        const events = result.rows.map(row => ({
            id: row.id,
            templateId: row.template_id,
            courseDates: row.course_dates,
            location: row.location,
            eventResponsible: row.event_responsible,
            applicationDeadline: row.application_deadline,
            spots: row.spots,
            status: row.status,
            notes: row.notes,
            lastModifiedBy: row.last_modified_by,
            lastModified: row.last_modified,
            sourceFiles: row.source_files
        }));

        const exportObj = {
            events: events,
            metadata: {
                exportedAt: new Date().toISOString(),
                count: events.length
            }
        };

        const exportPath = path.join(__dirname, '../data/hemvarn_course_events_exported.json');

        fs.writeFileSync(exportPath, JSON.stringify(exportObj, null, 4));

        console.log(`Successfully exported ${events.length} course events to:`);
        console.log(exportPath);

    } catch (error) {
        console.error('Error exporting course events:', error);
    } finally {
        await pool.end();
    }
};

exportCourseEvents();
