// project-analyzer.js
const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

async function analyzeProject(projectPath) {
  console.log('📁 Анализирую структуру проекта...');
  
  // Получаем список важных файлов
  const importantFiles = await findImportantFiles(projectPath);
  
  // Читаем содержимое ключевых файлов (первые 500 строк)
  let projectContext = "# Анализ проекта\n\n";
  
  for (const file of importantFiles.slice(0, 10)) { // Ограничиваем 10 файлами
    try {
      const content = await fs.readFile(file, 'utf-8');
      const lines = content.split('\n').slice(0, 50).join('\n');
      projectContext += `## Файл: ${file}\n\`\`\`\n${lines}\n\`\`\`\n\n`;
    } catch (err) {
      console.log(`⚠️ Не удалось прочитать: ${file}`);
    }
  }
  
  // Сохраняем временный файл
  await fs.writeFile('_project_analysis.txt', projectContext);
  
  // Анализируем через Qwen
  console.log('🤖 Отправляю на анализ Qwen...');
  exec(`qwen code --file _project_analysis.txt "Проанализируй этот проект. Найди: 1) Ошибки и баги, 2) Проблемы архитектуры, 3) Возможности оптимизации, 4) Нарушения best practices. Предложи конкретные исправления."`,
    (error, stdout, stderr) => {
      if (error) {
        console.error('❌ Ошибка:', error);
        return;
      }
      console.log('📝 Результаты анализа:');
      console.log(stdout);
      
      // Сохраняем результат
      fs.writeFile('_qwen_analysis_report.txt', stdout);
      console.log('✅ Отчёт сохранён в _qwen_analysis_report.txt');
    }
  );
}

async function findImportantFiles(dir) {
  const importantExtensions = ['.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.cpp', '.go'];
  const ignoreDirs = ['node_modules', '.git', 'dist', 'build'];
  
  const files = [];
  
  async function scan(currentPath) {
    const items = await fs.readdir(currentPath);
    
    for (const item of items) {
      const fullPath = path.join(currentPath, item);
      const stat = await fs.stat(fullPath);
      
      if (stat.isDirectory()) {
        if (!ignoreDirs.includes(item)) {
          await scan(fullPath);
        }
      } else if (importantExtensions.some(ext => item.endsWith(ext))) {
        files.push(fullPath);
      }
    }
  }
  
  await scan(dir);
  return files;
}

// Запуск
analyzeProject('.').catch(console.error);