export const messages = {
  en: {
    language: {
      names: {
        ar: 'العربية',
        en: 'English',
        zh: '中文'
      }
    },
    common: {
      appName: 'MIROFISH',
      stepIndicator: 'Step {current}/{total}',
      viewModes: {
        graph: 'Graph',
        split: 'Split',
        workbench: 'Workbench'
      },
      steps: {
        graphBuild: 'Graph Build',
        environmentSetup: 'Environment Setup',
        startSimulation: 'Start Simulation',
        reportGeneration: 'Report Generation',
        deepInteraction: 'Deep Interaction'
      },
      status: {
        error: 'Error',
        ready: 'Ready',
        buildingGraph: 'Building Graph',
        generatingOntology: 'Generating Ontology',
        initializing: 'Initializing',
        completed: 'Completed',
        running: 'Running',
        processing: 'Processing',
        preparing: 'Preparing',
        generating: 'Generating'
      }
    },
    home: {
      nav: {
        github: 'Visit our GitHub'
      },
      hero: {
        tag: 'Lean general-purpose collective intelligence engine',
        version: '/ v0.1 preview',
        titleLine1: 'Upload any report',
        titleLine2: 'and simulate the future instantly',
        descriptionStart: 'Even with only a short passage,',
        descriptionMiddle: 'can automatically build a parallel world from real-world seeds with up to',
        millionAgents: 'one million agents',
        descriptionEnd: 'and search for a dynamic',
        localOptimum: '"local optimum"',
        slogan: 'Let the future rehearse inside agent societies, and let decisions win after countless rounds.'
      },
      dashboard: {
        systemStatus: 'System Status',
        readyTitle: 'Ready',
        readyDesc: 'The prediction engine is standing by. Upload multiple unstructured files to initialize a simulation sequence.',
        metrics: {
          lowCostTitle: 'Low Cost',
          lowCostValue: 'Typical simulations average about $5 per run',
          highAvailabilityTitle: 'High Availability',
          highAvailabilityValue: 'Supports simulations with up to one million agents'
        },
        workflowTitle: 'Workflow Sequence',
        workflow: {
          graphBuildDesc: 'Extract reality seeds, inject personal and collective memory, and build GraphRAG.',
          environmentSetupDesc: 'Extract entities and relations, generate personas, and inject simulation parameters.',
          startSimulationDesc: 'Run dual-platform simulations, parse prediction goals, and update temporal memory.',
          reportGenerationDesc: 'Let ReportAgent use its toolset to inspect the post-simulation world in depth.',
          deepInteractionDesc: 'Talk to any simulated persona or continue the analysis with ReportAgent.'
        }
      },
      console: {
        seedLabel: '01 / Reality Seeds',
        supportedFormats: 'Formats: PDF, MD, TXT',
        uploadTitle: 'Drag files here',
        uploadHint: 'or click to browse your file system',
        inputParameters: 'Input Parameters',
        promptLabel: '>_ 02 / Simulation Prompt',
        promptPlaceholder: '// Describe your simulation or prediction request in natural language',
        engine: 'Engine: MiroFish-V1.0',
        startEngine: 'Start Engine',
        initializing: 'Initializing...'
      }
    },
    history: {
      title: 'Simulation History',
      status: {
        graphBuild: 'Graph Build',
        environmentSetup: 'Environment Setup',
        report: 'Report'
      },
      filesMore: '+{count} files',
      noFiles: 'No files yet',
      loading: 'Loading...',
      simulationRequirement: 'Simulation Requirement',
      relatedFiles: 'Related Files',
      noRelatedFiles: 'No related files',
      replay: 'Replay',
      replayHint: 'Step 3 “Start Simulation” and Step 5 “Deep Interaction” must be launched while the environment is running and cannot be replayed later.',
      notStarted: 'Not started',
      rounds: '{current}/{total} rounds',
      unnamedSimulation: 'Untitled simulation',
      unknownFile: 'Unknown file',
      noValue: 'None'
    },
    graph: {
      title: 'Graph Relationship Visualization',
      refresh: 'Refresh',
      toggleMaximize: 'Maximize / Restore',
      updating: 'Updating in real time...',
      memoryUpdating: 'GraphRAG short-term and long-term memory is updating in real time',
      finishedHint: 'A small amount of post-processing is still running. Refresh the graph in a moment.',
      closeHint: 'Dismiss hint',
      nodeDetails: 'Node Details',
      relationship: 'Relationship',
      name: 'Name',
      uuid: 'UUID',
      created: 'Created',
      properties: 'Properties',
      none: 'None',
      summary: 'Summary',
      labels: 'Labels',
      selfRelations: 'Self Relations',
      items: '{count} items',
      fact: 'Fact',
      type: 'Type',
      episodes: 'Episodes',
      label: 'Label',
      unknown: 'Unknown',
      validFrom: 'Valid From',
      loadingGraph: 'Loading graph data...',
      waitingOntology: 'Waiting for ontology generation...',
      entityTypes: 'Entity Types',
      showEdgeLabels: 'Show Edge Labels',
      relatedTo: 'RELATED_TO'
    },
    step1: {
      ontologyGeneration: 'Ontology Generation',
      graphRagBuild: 'GraphRAG Build',
      buildCompleted: 'Build Complete',
      completed: 'Completed',
      processing: 'In Progress',
      pending: 'Pending',
      ontologyDescription: 'The LLM analyzes the documents and the simulation requirement, extracts the reality seeds, and generates a suitable ontology automatically.',
      analyzingDocs: 'Analyzing documents...',
      generatedEntityTypes: 'GENERATED ENTITY TYPES',
      generatedRelationTypes: 'GENERATED RELATION TYPES',
      graphBuildDescription: 'Use the generated ontology to chunk the documents, build a knowledge graph in Zep, extract entities and relations, and form temporal memory plus community summaries.',
      entityNodes: 'Entity Nodes',
      relationEdges: 'Relation Edges',
      schemaTypes: 'Schema Types',
      completeDescription: 'Graph construction is complete. Continue to the next step to prepare the simulation environment.',
      creating: 'Creating...',
      enterEnvironmentSetup: 'Enter Environment Setup ➝',
      systemDashboard: 'SYSTEM DASHBOARD',
      noProject: 'NO_PROJECT',
      missingProjectInfo: 'Missing project or graph metadata.',
      createSimulationFailed: 'Failed to create simulation',
      createSimulationError: 'Simulation creation error'
    }
  },
  ar: {
    language: {
      names: {
        ar: 'العربية',
        en: 'English',
        zh: '中文'
      }
    },
    common: {
      appName: 'MIROFISH',
      stepIndicator: 'الخطوة {current}/{total}',
      viewModes: {
        graph: 'الرسم',
        split: 'لوحتان',
        workbench: 'مساحة العمل'
      },
      steps: {
        graphBuild: 'بناء الرسم المعرفي',
        environmentSetup: 'إعداد البيئة',
        startSimulation: 'بدء المحاكاة',
        reportGeneration: 'توليد التقرير',
        deepInteraction: 'التفاعل العميق'
      },
      status: {
        error: 'خطأ',
        ready: 'جاهز',
        buildingGraph: 'جارٍ بناء الرسم',
        generatingOntology: 'جارٍ توليد الأنطولوجيا',
        initializing: 'جارٍ التهيئة',
        completed: 'مكتمل',
        running: 'قيد التشغيل',
        processing: 'قيد المعالجة',
        preparing: 'جارٍ الإعداد',
        generating: 'جارٍ التوليد'
      }
    },
    home: {
      nav: {
        github: 'زيارة GitHub'
      },
      hero: {
        tag: 'محرك ذكاء جماعي عام وخفيف',
        version: '/ إصدار معاينة v0.1',
        titleLine1: 'ارفع أي تقرير',
        titleLine2: 'واستكشف المستقبل فوراً',
        descriptionStart: 'حتى لو بدأت بفقرة واحدة فقط، يستطيع',
        descriptionMiddle: 'أن يبني عالماً موازياً من بذور الواقع يضم ما يصل إلى',
        millionAgents: 'مليون وكيل',
        descriptionEnd: 'مع حقن المتغيرات من منظور شامل للبحث عن',
        localOptimum: '«أفضل حل محلي»',
        slogan: 'دع المستقبل يُحاكى داخل جماعات الوكلاء، ولتخرج القرارات رابحة بعد جولات لا تُحصى.'
      },
      dashboard: {
        systemStatus: 'حالة النظام',
        readyTitle: 'جاهز',
        readyDesc: 'محرك التنبؤ في وضع الاستعداد. ارفع عدة ملفات غير مهيكلة لبدء سلسلة محاكاة جديدة.',
        metrics: {
          lowCostTitle: 'تكلفة منخفضة',
          lowCostValue: 'متوسط المحاكاة المعتادة يقارب 5 دولارات لكل تشغيل',
          highAvailabilityTitle: 'اعتمادية عالية',
          highAvailabilityValue: 'يدعم محاكاة يصل حجمها إلى مليون وكيل'
        },
        workflowTitle: 'تسلسل العمل',
        workflow: {
          graphBuildDesc: 'استخراج بذور الواقع، وحقن الذاكرة الفردية والجماعية، وبناء GraphRAG.',
          environmentSetupDesc: 'استخراج الكيانات والعلاقات، وتوليد الشخصيات، وحقن معلمات المحاكاة.',
          startSimulationDesc: 'تشغيل محاكاة متوازية على منصتين، وتحليل أهداف التنبؤ، وتحديث الذاكرة الزمنية.',
          reportGenerationDesc: 'تمكين ReportAgent من استخدام أدواته لتحليل العالم بعد المحاكاة بعمق.',
          deepInteractionDesc: 'التحدث مع أي شخصية داخل العالم المحاكى أو متابعة التحليل مع ReportAgent.'
        }
      },
      console: {
        seedLabel: '01 / بذور الواقع',
        supportedFormats: 'الصيغ المدعومة: PDF, MD, TXT',
        uploadTitle: 'اسحب الملفات إلى هنا',
        uploadHint: 'أو انقر لاستعراض نظام الملفات',
        inputParameters: 'معلمات الإدخال',
        promptLabel: '>_ 02 / وصف المحاكاة',
        promptPlaceholder: '// اكتب طلب المحاكاة أو التنبؤ بلغة طبيعية',
        engine: 'المحرك: MiroFish-V1.0',
        startEngine: 'تشغيل المحرك',
        initializing: 'جارٍ التهيئة...'
      }
    },
    history: {
      title: 'سجل المحاكاة',
      status: {
        graphBuild: 'بناء الرسم',
        environmentSetup: 'إعداد البيئة',
        report: 'التقرير'
      },
      filesMore: '+{count} ملفات',
      noFiles: 'لا توجد ملفات',
      loading: 'جارٍ التحميل...',
      simulationRequirement: 'متطلب المحاكاة',
      relatedFiles: 'الملفات المرتبطة',
      noRelatedFiles: 'لا توجد ملفات مرتبطة',
      replay: 'إعادة التشغيل',
      replayHint: 'يجب تشغيل الخطوة 3 «بدء المحاكاة» والخطوة 5 «التفاعل العميق» أثناء عمل البيئة، ولا يمكن إعادة تشغيلهما لاحقاً.',
      notStarted: 'لم تبدأ بعد',
      rounds: '{current}/{total} جولة',
      unnamedSimulation: 'محاكاة بلا اسم',
      unknownFile: 'ملف غير معروف',
      noValue: 'لا يوجد'
    },
    graph: {
      title: 'تصوير علاقات الرسم المعرفي',
      refresh: 'تحديث',
      toggleMaximize: 'تكبير / استعادة',
      updating: 'يتم التحديث آنياً...',
      memoryUpdating: 'يتم تحديث ذاكرة GraphRAG القصيرة والطويلة في الوقت الفعلي',
      finishedHint: 'ما زال جزء صغير من المعالجة مستمراً. حدِّث الرسم بعد قليل.',
      closeHint: 'إغلاق التنبيه',
      nodeDetails: 'تفاصيل العقدة',
      relationship: 'العلاقة',
      name: 'الاسم',
      uuid: 'المعرّف',
      created: 'أُنشئ في',
      properties: 'الخصائص',
      none: 'لا يوجد',
      summary: 'الملخص',
      labels: 'الوسوم',
      selfRelations: 'علاقات ذاتية',
      items: '{count} عنصر',
      fact: 'الحقيقة',
      type: 'النوع',
      episodes: 'الحلقات',
      label: 'الوسم',
      unknown: 'غير معروف',
      validFrom: 'ساري من',
      loadingGraph: 'جارٍ تحميل بيانات الرسم...',
      waitingOntology: 'في انتظار توليد الأنطولوجيا...',
      entityTypes: 'أنواع الكيانات',
      showEdgeLabels: 'إظهار وسوم الحواف',
      relatedTo: 'مرتبط_بـ'
    },
    step1: {
      ontologyGeneration: 'توليد الأنطولوجيا',
      graphRagBuild: 'بناء GraphRAG',
      buildCompleted: 'اكتمل البناء',
      completed: 'مكتمل',
      processing: 'قيد التنفيذ',
      pending: 'بانتظار البدء',
      ontologyDescription: 'يقوم النموذج بتحليل المستندات وطلب المحاكاة واستخراج بذور الواقع ثم إنشاء أنطولوجيا مناسبة تلقائياً.',
      analyzingDocs: 'جارٍ تحليل المستندات...',
      generatedEntityTypes: 'أنواع الكيانات المولَّدة',
      generatedRelationTypes: 'أنواع العلاقات المولَّدة',
      graphBuildDescription: 'باستخدام الأنطولوجيا المولَّدة، تُقسَّم المستندات تلقائياً ويُبنى الرسم المعرفي في Zep مع استخراج الكيانات والعلاقات وتكوين الذاكرة الزمنية وملخصات المجتمعات.',
      entityNodes: 'عُقد الكيانات',
      relationEdges: 'حواف العلاقات',
      schemaTypes: 'أنواع المخطط',
      completeDescription: 'اكتمل بناء الرسم. انتقل إلى الخطوة التالية لإعداد بيئة المحاكاة.',
      creating: 'جارٍ الإنشاء...',
      enterEnvironmentSetup: 'الانتقال إلى إعداد البيئة ➝',
      systemDashboard: 'لوحة النظام',
      noProject: 'لا يوجد مشروع',
      missingProjectInfo: 'بيانات المشروع أو الرسم ناقصة.',
      createSimulationFailed: 'فشل إنشاء المحاكاة',
      createSimulationError: 'حدث خطأ أثناء إنشاء المحاكاة'
    }
  },
  zh: {
    language: {
      names: {
        ar: 'العربية',
        en: 'English',
        zh: '中文'
      }
    },
    common: {
      appName: 'MIROFISH',
      stepIndicator: 'Step {current}/{total}',
      viewModes: {
        graph: '图谱',
        split: '双栏',
        workbench: '工作台'
      },
      steps: {
        graphBuild: '图谱构建',
        environmentSetup: '环境搭建',
        startSimulation: '开始模拟',
        reportGeneration: '报告生成',
        deepInteraction: '深度互动'
      },
      status: {
        error: '错误',
        ready: '就绪',
        buildingGraph: '图谱构建中',
        generatingOntology: '本体生成中',
        initializing: '初始化中',
        completed: '已完成',
        running: '运行中',
        processing: '处理中',
        preparing: '准备中',
        generating: '生成中'
      }
    },
    home: {
      nav: {
        github: '访问我们的 GitHub'
      },
      hero: {
        tag: '简洁通用的群体智能引擎',
        version: '/ v0.1 预览版',
        titleLine1: '上传任意报告',
        titleLine2: '即刻推演未来',
        descriptionStart: '即使只有一段文字，',
        descriptionMiddle: '也能基于现实种子自动生成最多',
        millionAgents: '百万级 Agent',
        descriptionEnd: '构成的平行世界，并寻找动态环境下的',
        localOptimum: '“局部最优解”',
        slogan: '让未来在 Agent 群中预演，让决策在百战后胜出。'
      },
      dashboard: {
        systemStatus: '系统状态',
        readyTitle: '准备就绪',
        readyDesc: '预测引擎待命中，可上传多份非结构化数据以初始化模拟序列。',
        metrics: {
          lowCostTitle: '低成本',
          lowCostValue: '常规模拟平均 5 美元 / 次',
          highAvailabilityTitle: '高可用',
          highAvailabilityValue: '最多支持百万级 Agent 模拟'
        },
        workflowTitle: '工作流序列',
        workflow: {
          graphBuildDesc: '现实种子提取、个体与群体记忆注入以及 GraphRAG 构建。',
          environmentSetupDesc: '实体关系抽取、人设生成与仿真参数注入。',
          startSimulationDesc: '双平台并行模拟、解析预测需求并动态更新时序记忆。',
          reportGenerationDesc: '由 ReportAgent 使用工具集与模拟后环境进行深度交互。',
          deepInteractionDesc: '与模拟世界任意角色或 ReportAgent 持续对话。'
        }
      },
      console: {
        seedLabel: '01 / 现实种子',
        supportedFormats: '支持格式: PDF, MD, TXT',
        uploadTitle: '拖拽文件上传',
        uploadHint: '或点击浏览文件系统',
        inputParameters: '输入参数',
        promptLabel: '>_ 02 / 模拟提示词',
        promptPlaceholder: '// 用自然语言输入模拟或预测需求',
        engine: '引擎: MiroFish-V1.0',
        startEngine: '启动引擎',
        initializing: '初始化中...'
      }
    },
    history: {
      title: '推演记录',
      status: {
        graphBuild: '图谱构建',
        environmentSetup: '环境搭建',
        report: '分析报告'
      },
      filesMore: '+{count} 个文件',
      noFiles: '暂无文件',
      loading: '加载中...',
      simulationRequirement: '模拟需求',
      relatedFiles: '关联文件',
      noRelatedFiles: '暂无关联文件',
      replay: '推演回放',
      replayHint: 'Step3「开始模拟」与 Step5「深度互动」需在运行中启动，不支持历史回放。',
      notStarted: '未开始',
      rounds: '{current}/{total} 轮',
      unnamedSimulation: '未命名模拟',
      unknownFile: '未知文件',
      noValue: '无'
    },
    graph: {
      title: 'Graph Relationship Visualization',
      refresh: '刷新',
      toggleMaximize: '最大化 / 还原',
      updating: '实时更新中...',
      memoryUpdating: 'GraphRAG 长短期记忆实时更新中',
      finishedHint: '还有少量内容处理中，建议稍后手动刷新图谱。',
      closeHint: '关闭提示',
      nodeDetails: '节点详情',
      relationship: '关系',
      name: '名称',
      uuid: 'UUID',
      created: '创建时间',
      properties: '属性',
      none: '无',
      summary: '摘要',
      labels: '标签',
      selfRelations: '自环关系',
      items: '{count} 项',
      fact: '事实',
      type: '类型',
      episodes: '事件集',
      label: '标签',
      unknown: '未知',
      validFrom: '生效时间',
      loadingGraph: '图谱数据加载中...',
      waitingOntology: '等待本体生成...',
      entityTypes: '实体类型',
      showEdgeLabels: '显示边标签',
      relatedTo: 'RELATED_TO'
    },
    step1: {
      ontologyGeneration: '本体生成',
      graphRagBuild: 'GraphRAG 构建',
      buildCompleted: '构建完成',
      completed: '已完成',
      processing: '生成中',
      pending: '等待',
      ontologyDescription: 'LLM 分析文档内容与模拟需求，提取现实种子并自动生成合适的本体结构。',
      analyzingDocs: '正在分析文档...',
      generatedEntityTypes: '生成的实体类型',
      generatedRelationTypes: '生成的关系类型',
      graphBuildDescription: '基于生成的本体自动分块文档，在 Zep 中构建知识图谱并形成时序记忆与社区摘要。',
      entityNodes: '实体节点',
      relationEdges: '关系边',
      schemaTypes: 'Schema 类型',
      completeDescription: '图谱构建已完成，请进入下一步进行模拟环境搭建。',
      creating: '创建中...',
      enterEnvironmentSetup: '进入环境搭建 ➝',
      systemDashboard: '系统看板',
      noProject: '无项目',
      missingProjectInfo: '缺少项目或图谱信息。',
      createSimulationFailed: '创建模拟失败',
      createSimulationError: '创建模拟异常'
    }
  }
}

export default messages
