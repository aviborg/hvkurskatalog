import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import pool from './config/db.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const exportData = async () => {
    try {
        console.log('Fetching course templates from database...');

        const result = await pool.query('SELECT * FROM course_templates ORDER BY name ASC');

        const templates = result.rows.map(row => ({
            id: row.id,
            name: row.name,
            shortName: row.short_name,
            category: row.category,
            courseCode: row.course_code,
            description: row.description,
            targetAudience: row.target_audience,
            syllabus: row.syllabus,
            purpose: row.purpose,
            primaryLearningObjective: row.primary_learning_objective,
            secondaryLearningObjectives: row.secondary_learning_objectives,
            examination: row.examination,
            prerequisites: row.prerequisites,
            literature: row.literature,
            additionalInfo: row.additional_info,
            typicalDuration: row.typical_duration,
            courseResponsible: row.course_responsible,
            baseTemplateIds: row.base_template_ids,
            sourceFiles: row.source_files,
            lastModifiedBy: row.last_modified_by,
            lastModified: row.last_modified
        }));

        const exportObj = {
            templates: templates,
            metadata: {
                exportedAt: new Date().toISOString(),
                count: templates.length
            }
        };

        const exportPath = path.join(__dirname, '../data/hemvarn_course_templates_enriched_exported.json');

        fs.writeFileSync(exportPath, JSON.stringify(exportObj, null, 4));

        console.log(`Successfully exported ${templates.length} templates to:`);
        console.log(exportPath);

    } catch (error) {
        console.error('Error exporting data:', error);
    } finally {
        await pool.end();
    }
};

exportData();
