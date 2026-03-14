use std::{fs, path::PathBuf};

use anyhow::Result;
use chrono::Local;
use printpdf::{BuiltinFont, Layer, Mm, Op, PdfDocument, PdfPage, Point, Pt, TextItem};

use crate::domain::models::Dossier;

#[derive(Default)]
pub struct PdfService;

impl PdfService {
    pub fn new() -> Self {
        Self
    }

    pub fn generate(&self, dossier: &Dossier) -> Result<String> {
        let mut doc = PdfDocument::new(&format!("Dossier {}", dossier.suspect.full_name));
        let layer = Layer::new("main");
        let layer_id = doc.add_layer(&layer);
        let mut ops: Vec<Op> = Vec::new();

        ops.push(Op::BeginLayer { layer_id: layer_id.clone() });
        ops.push(Op::StartTextSection);
        ops.extend(write_line(20.0, 280.0, 22.0, &format!("CONFIDENTIAL DOSSIER :: {}", dossier.case.classification)));
        ops.extend(write_line(20.0, 268.0, 18.0, &dossier.suspect.full_name.to_uppercase()));
        ops.extend(write_line(20.0, 259.0, 10.0, &format!("Alias: {}", empty_dash(&dossier.suspect.alias_name))));
        ops.extend(write_line(120.0, 259.0, 10.0, &format!("Role: {}", empty_dash(&dossier.suspect.role))));
        ops.extend(write_line(20.0, 252.0, 10.0, &format!("Status: {}", empty_dash(&dossier.suspect.status))));
        ops.extend(write_line(120.0, 252.0, 10.0, &format!("Suspicion Level: {}%", dossier.suspect.suspicion_level)));
        ops.extend(write_line(20.0, 245.0, 10.0, &format!("Location: {}", empty_dash(&dossier.suspect.location))));
        ops.extend(write_block(20.0, 233.0, "Case Summary", &dossier.case.summary, 85.0));
        ops.extend(write_block(20.0, 186.0, "Description", &dossier.suspect.description, 80.0));
        ops.extend(write_block(110.0, 233.0, "Field Notes", &dossier.suspect.notes, 127.0));

        let evidence_text = dossier.evidence.iter().map(|item| format!("• {} [{}] — {}", item.title, item.status, item.details)).collect::<Vec<_>>().join("\n");
        ops.extend(write_block(20.0, 145.0, "Evidence", &evidence_text, 55.0));

        let events_text = dossier.events.iter().map(|item| format!("• {} — {}", item.event_date, item.title)).collect::<Vec<_>>().join("\n");
        ops.extend(write_block(110.0, 145.0, "Timeline", &events_text, 55.0));

        let relations_text = dossier.relations.iter().map(|item| format!("• {} / {} / {}%", item.target_label, item.relation_type, item.confidence)).collect::<Vec<_>>().join("\n");
        ops.extend(write_block(20.0, 82.0, "Connections", &relations_text, 38.0));
        ops.extend(write_line(20.0, 20.0, 9.0, &format!("Generated {}", Local::now().format("%Y-%m-%d %H:%M:%S"))));
        ops.push(Op::EndTextSection);
        ops.push(Op::EndLayer { layer_id });

        let page = PdfPage::new(Mm(210.0), Mm(297.0), ops);
        doc.with_pages(vec![page]);

        let output_dir = std::env::current_dir()?.join("app_data").join("exports");
        fs::create_dir_all(&output_dir)?;
        let filename = format!(
            "{}_{}.pdf",
            dossier.suspect.full_name.replace(' ', "_"),
            Local::now().format("%Y%m%d_%H%M%S")
        );
        let path = output_dir.join(filename);
        let bytes = doc.save(&Default::default(), &mut Vec::new());
        fs::write(&path, bytes)?;
        Ok(path.to_string_lossy().to_string())
    }
}

fn write_line(x_mm: f32, y_mm: f32, size_pt: f32, text: &str) -> Vec<Op> {
    vec![
        Op::SetFontSizeBuiltinFont { size: Pt(size_pt), font: BuiltinFont::HelveticaBold },
        Op::SetTextCursor { pos: Point::new(Mm(x_mm), Mm(y_mm)) },
        Op::WriteTextBuiltinFont { items: vec![TextItem::Text(text.to_string())], font: BuiltinFont::HelveticaBold },
    ]
}

fn write_block(x_mm: f32, y_mm: f32, title: &str, content: &str, height: f32) -> Vec<Op> {
    let mut ops = vec![];
    ops.extend(write_line(x_mm, y_mm, 11.0, title));
    let mut current_y = y_mm - 6.0;
    for line in wrap(content, 48) {
        if current_y < y_mm - height { break; }
        ops.push(Op::SetFontSizeBuiltinFont { size: Pt(9.0), font: BuiltinFont::Helvetica });
        ops.push(Op::SetTextCursor { pos: Point::new(Mm(x_mm), Mm(current_y)) });
        ops.push(Op::WriteTextBuiltinFont { items: vec![TextItem::Text(line)], font: BuiltinFont::Helvetica });
        current_y -= 4.2;
    }
    ops
}

fn wrap(content: &str, max_chars: usize) -> Vec<String> {
    let mut lines = Vec::new();
    for paragraph in content.split('\n') {
        let mut current = String::new();
        for word in paragraph.split_whitespace() {
            if current.len() + word.len() + 1 > max_chars {
                lines.push(current.trim().to_string());
                current.clear();
            }
            current.push_str(word);
            current.push(' ');
        }
        if !current.trim().is_empty() {
            lines.push(current.trim().to_string());
        }
    }
    if lines.is_empty() {
        lines.push("—".to_string());
    }
    lines
}

fn empty_dash(value: &str) -> String {
    if value.trim().is_empty() { "—".into() } else { value.into() }
}
