import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import pool from './config/db.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const importData = async () => {
    try {
        const filePath = path.join(__dirname, '../data/hemvarn_course_templates_enriched.json');
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        const templates = data.templates;

        console.log(`Starting import of ${templates.length} templates...`);

        for (const template of templates) {
            const {
                id, name, shortName, category, courseCode, description,
                targetAudience, syllabus, purpose, primaryLearningObjective,
                secondaryLearningObjectives, examination, prerequisites,
                literature, additionalInfo, typicalDuration, courseResponsible,
                baseTemplateIds, sourceFiles, lastModifiedBy, lastModified
            } = template;

            const queryText = `
                INSERT INTO course_templates (
                    id, name, short_name, category, course_code, description,
                    target_audience, syllabus, purpose, primary_learning_objective,
                    secondary_learning_objectives, examination, prerequisites,
                    literature, additional_info, typical_duration, course_responsible,
                    base_template_ids, source_files, last_modified_by, last_modified
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    short_name = EXCLUDED.short_name,
                    category = EXCLUDED.category,
                    course_code = EXCLUDED.course_code,
                    description = EXCLUDED.description,
                    target_audience = EXCLUDED.target_audience,
                    syllabus = EXCLUDED.syllabus,
                    purpose = EXCLUDED.purpose,
                    primary_learning_objective = EXCLUDED.primary_learning_objective,
                    secondary_learning_objectives = EXCLUDED.secondary_learning_objectives,
                    examination = EXCLUDED.examination,
                    prerequisites = EXCLUDED.prerequisites,
                    literature = EXCLUDED.literature,
                    additional_info = EXCLUDED.additional_info,
                    typical_duration = EXCLUDED.typical_duration,
                    course_responsible = EXCLUDED.course_responsible,
                    base_template_ids = EXCLUDED.base_template_ids,
                    source_files = EXCLUDED.source_files,
                    last_modified_by = EXCLUDED.last_modified_by,
                    last_modified = EXCLUDED.last_modified;
            `;

            const values = [
                id, name, shortName, category, courseCode, description,
                targetAudience, syllabus, purpose, primaryLearningObjective,
                JSON.stringify(secondaryLearningObjectives || []),
                examination,
                JSON.stringify(prerequisites || []),
                JSON.stringify(literature || []),
                additionalInfo, typicalDuration, courseResponsible,
                JSON.stringify(baseTemplateIds || []),
                JSON.stringify(sourceFiles || []),
                lastModifiedBy, lastModified
            ];

            await pool.query(queryText, values);
            console.log(`Imported/Updated template: ${id}`);
        }

        console.log('Import completed successfully.');
    } catch (error) {
        console.error('Error importing data:', error);
    } finally {
        await pool.end();
    }
};

importData();
