/**
 * Harvest Harbor Plant Disease Knowledge Catalog
 * FALLBACK / OFFLINE STATIC DATA: Backend diseases.json is the authoritative single source of truth.
 * This catalog is retained for offline preview and educational fallback only.
 */

export const CROPS_LIST = [
  'All',
  'Apple',
  'Potato',
  'Tomato',
  'Corn',
  'Banana',
  'Grape',
  'Bell Pepper',
  'Cherry',
  'Peach',
  'Blueberry',
  'Wheat',
  'Strawberry',
  'Cabbage',
];

export const DISEASE_CATALOG = [
  {
    id: 'apple_black_rot',
    crop: 'Apple',
    disease: 'Black Rot (Frogeye Leaf Spot)',
    pathogen: 'Botryosphaeria obtusa',
    type: 'Fungal',
    severityRisk: 'Moderate to High',
    symptoms: [
      'Small purple flecks on leaf upper surface that enlarge into concentric rings resembling a "frog-eye".',
      'Fruit develops firm, brown rotting areas with concentric black rings.',
      'Bark cankers develop on infected twigs and limbs, serving as fungal reservoirs.',
    ],
    environmentalFactors: [
      'Warm temperatures (20°C–27°C) coupled with rainfall.',
      'Wet foliage sustained for 9 or more consecutive hours.',
      'Unhygienic orchard floor with mummified fruits and unpruned dead wood.',
    ],
    immediateActions: [
      'Prune dead or cankered twigs 15 cm below visible infection boundaries.',
      'Collect and incinerate/bury fallen mummified apples and infected leaf debris.',
      'Disinfect pruning shears in 70% alcohol between cuts to prevent mechanical spread.',
    ],
    prevention: [
      'Select resistant cultivars when establishing new orchard blocks.',
      'Consult local extension guidance regarding regionally approved preventive sprays during key canopy emergence stages.',
      'Optimize canopy pruning to maximize sunlight penetration and promote rapid leaf drying.',
    ],
  },
  {
    id: 'apple_scab',
    crop: 'Apple',
    disease: 'Apple Scab',
    pathogen: 'Venturia inaequalis',
    type: 'Fungal',
    severityRisk: 'High',
    symptoms: [
      'Olive-green to velvety dark brown lesions on the upper leaf surface.',
      'Leaves may become distorted, crinkled, and drop prematurely.',
      'Infected fruit exhibits scabby, corky, cracked blemishes lowering market quality.',
    ],
    environmentalFactors: [
      'Cool, wet spring conditions (13°C–24°C).',
      'Leaves remaining wet for 6 to 28 continuous hours depending on temperature.',
      'High overwintering ascospore load in fallen leaf litter.',
    ],
    immediateActions: [
      'Consider timely disease-management intervention based on local extension guidance and verified field assessment.',
      'Rake and shred or compost fallen apple leaves to accelerate overwintering spore decay.',
    ],
    prevention: [
      'Plant scab-resistant apple varieties (e.g., Liberty, Freedom, Enterprise).',
      'Apply flail mowing or urea spray (5%) to fallen leaves in late autumn to speed leaf breakdown.',
      'Space trees appropriately to ensure rapid morning canopy drying.',
    ],
  },
  {
    id: 'apple_rust',
    crop: 'Apple',
    disease: 'Cedar Apple Rust',
    pathogen: 'Gymnosporangium juniperi-virginianae',
    type: 'Fungal',
    severityRisk: 'Moderate',
    symptoms: [
      'Bright yellow-orange spots on upper leaf surfaces that enlarge and develop black pycnia.',
      'Cluster cups (aecia) form on the underside of leaves with thread-like projections.',
      'Premature defoliation and weakened fruit bud development in subsequent seasons.',
    ],
    environmentalFactors: [
      'Presence of Eastern Red Cedar or Juniper alternate hosts within 1–2 miles.',
      'Warm spring rain events triggering gelatinous spore horn emergence on cedar galls.',
    ],
    immediateActions: [
      'Inspect nearby juniper/cedar windbreaks and prune out visible rust galls in late winter.',
      'Consider regionally approved disease-management options and consult local agricultural extension guidance before treatment.',
    ],
    prevention: [
      'Remove susceptible red cedar trees within 500 meters of the commercial orchard boundary.',
      'Plant rust-immune or tolerant cultivars (e.g., Redfree, Williams Pride).',
    ],
  },
  {
    id: 'potato_early_blight',
    crop: 'Potato',
    disease: 'Early Blight',
    pathogen: 'Alternaria solani',
    type: 'Fungal',
    severityRisk: 'Moderate to High',
    symptoms: [
      'Dark brown to black necrotic spots with characteristic target-like concentric rings.',
      'Lower/older foliage affected first, yellowing and senescing prematurely.',
      'Tuber lesions appear sunken, dark, and leathery with a dry corky rot beneath the skin.',
    ],
    environmentalFactors: [
      'Alternating wet and dry periods with warm days (24°C–29°C) and heavy night dews.',
      'Plants under physiological stress (drought, nitrogen deficit, heavy tuber bulking).',
    ],
    immediateActions: [
      'Avoid overhead irrigation late in the afternoon to prevent extended overnight leaf wetness.',
      'Consider regionally approved disease-management options and consult local agricultural extension guidance before treatment.',
      'Remove and destroy heavily diseased volunteer potato plants in the perimeter.',
    ],
    prevention: [
      'Maintain certified disease-free seed tubers.',
      'Practice minimum 3-year crop rotation with non-solanaceous crops (cereals, legumes).',
      'Ensure balanced nitrogen fertilization to avoid premature canopy aging.',
    ],
  },
  {
    id: 'potato_late_blight',
    crop: 'Potato',
    disease: 'Late Blight',
    pathogen: 'Phytophthora infestans',
    type: 'Oomycete',
    severityRisk: 'Critical / Extreme',
    symptoms: [
      'Water-soaked pale green or dark brown lesions rapidly expanding on leaf tips and margins.',
      'Delicate white fungal-like sporulation visible on the underside of lesions during humid mornings.',
      'Entire vines turn black, collapse, and give off an unmistakable rotting odor within days.',
    ],
    environmentalFactors: [
      'Cool to moderate temperatures (12°C–20°C) with persistent relative humidity above 90%.',
      'Fog, heavy dew, or prolonged rainy spells.',
    ],
    immediateActions: [
      'Flag suspect plants for field scouting; consult regional agricultural extension specialists.',
      'Consider timely disease-management intervention based on local extension guidance and verified field assessment.',
      'Kill vine canopy before harvest to prevent motile zoospores from washing down into tubers.',
    ],
    prevention: [
      'Destroy all cull piles and volunteer potatoes before spring planting.',
      'Utilize late blight forecast decision-support tools (e.g. BlightCast).',
      'Hilling soil deeply over tubers to create a physical filter against washing spores.',
    ],
  },
  {
    id: 'tomato_early_blight',
    crop: 'Tomato',
    disease: 'Early Blight',
    pathogen: 'Alternaria linariae / solani',
    type: 'Fungal',
    severityRisk: 'Moderate to High',
    symptoms: [
      'Circular brown spots with distinct concentric rings ("target board" pattern) on older leaves.',
      'Chlorotic yellow halos surrounding spots that coalesce causing complete leaf drop.',
      'Sunken dark lesions at the stem base or fruit stem attachment point.',
    ],
    environmentalFactors: [
      'High humidity, warm temperatures (24°C–30°C), and extended morning dew.',
      'Rain splashing soil particles containing fungal spores onto lower leaves.',
    ],
    immediateActions: [
      'Strip lower leaves touching the soil surface up to 30 cm off the ground.',
      'Switch strictly to drip irrigation or soaker hoses; cease all overhead spraying.',
      'Consider regionally approved protective or bio-management options under local agronomist guidance.',
    ],
    prevention: [
      'Mulch heavily with straw or plastic sheeting to create a physical barrier over the soil.',
      'Stake or trellis tomato vines to maintain upright posture and optimum air circulation.',
      'Rotate fields for at least 3 years away from tomatoes, potatoes, eggplants, and peppers.',
    ],
  },
  {
    id: 'tomato_late_blight',
    crop: 'Tomato',
    disease: 'Late Blight',
    pathogen: 'Phytophthora infestans',
    type: 'Oomycete',
    severityRisk: 'Critical',
    symptoms: [
      'Greasy, dark water-soaked patches on leaves that dry into brown papery necrosis.',
      'White cottony spore growth on the underside of affected leaves in humid air.',
      'Firm, dark brown bumpy shoulders on green and ripe tomato fruits.',
    ],
    environmentalFactors: [
      'Cool damp weather (15°C–22°C) with relative humidity near 100%.',
      'Cloudy overcast periods with minimal sun exposure.',
    ],
    immediateActions: [
      'Bag and destroy infected plant sections on dry afternoons to minimize aerial spore drift.',
      'Do not compost infected plants; incinerate or dispose in sealed municipal waste bags.',
      'Evaluate regionally approved disease-management options and consult certified crop advisors before treatment.',
    ],
    prevention: [
      'Plant resistant tomato varieties (e.g., Defiant, Mountain Merit, Iron Lady).',
      'Ensure wide spacing between plants (at least 60–90 cm).',
      'Inspect crops twice weekly during wet, cool weather fronts.',
    ],
  },
  {
    id: 'tomato_septoria_leaf_spot',
    crop: 'Tomato',
    disease: 'Septoria Leaf Spot',
    pathogen: 'Septoria lycopersici',
    type: 'Fungal',
    severityRisk: 'Moderate',
    symptoms: [
      'Numerous small circular spots (1–3 mm) with dark brown margins and sunken grayish centers.',
      'Tiny black specks (pycnidia) clearly visible inside the center of mature spots.',
      'Progressive bottom-up leaf yellowing and severe defoliation exposing fruit to sunscald.',
    ],
    environmentalFactors: [
      'Wet weather with temperatures between 20°C and 25°C.',
      'Water splashing from soil or neighboring diseased leaves.',
    ],
    immediateActions: [
      'Prune infected lower foliage as soon as the first few spots are detected.',
      'Consider canopy protection strategies recommended by local extension services if disease pressure remains high.',
    ],
    prevention: [
      'Organic mulch layer of 5–8 cm over soil under all tomato trellises.',
      'Avoid working among wet plants to prevent spreading sticky spores on hands and tools.',
    ],
  },
  {
    id: 'corn_gray_leaf_spot',
    crop: 'Corn',
    disease: 'Gray Leaf Spot',
    pathogen: 'Cercospora zeae-maydis',
    type: 'Fungal',
    severityRisk: 'High',
    symptoms: [
      'Small, tan, rectangular lesions restricted by leaf veins giving them distinct parallel edges.',
      'Lesions expand into long gray-tan strips that coalesce and blight entire leaf blades.',
      'Severe blighting prematurely shuts down grain fill and causes stalk lodging.',
    ],
    environmentalFactors: [
      'Prolonged periods of high humidity (>90%) and warm temperatures (25°C–32°C).',
      'Conservation tillage with high corn residue left on the soil surface.',
    ],
    immediateActions: [
      'Assess lesion progression relative to the ear leaf at VT-R1 growth stages.',
      'If lesions progress toward the ear leaf before tasseling, consult local economic thresholds and extension advisors.',
    ],
    prevention: [
      'Select hybrid corn varieties with high genetic resistance ratings.',
      'Rotate with non-host crops like soybeans or small grains to reduce residue inoculum.',
      'Tillage practices that incorporate corn residue to accelerate fungal decomposition.',
    ],
  },
  {
    id: 'corn_rust',
    crop: 'Corn',
    disease: 'Common Rust',
    pathogen: 'Puccinia sorghi',
    type: 'Fungal',
    severityRisk: 'Moderate',
    symptoms: [
      'Cinnamon-brown, powdery, elongated pustules (uredinia) on both upper and lower leaf surfaces.',
      'Pustules rupture the epidermis, releasing millions of rusty-colored airborne spores.',
      'Leaves yellow and desiccate under heavy infection pressure.',
    ],
    environmentalFactors: [
      'Cool to moderate temperatures (16°C–24°C) with high relative humidity (>95%).',
      'Southern storm fronts carrying spores northward during the vegetative season.',
    ],
    immediateActions: [
      'Scout whorl and ear leaves; refer to regional university extension thresholds before considering intervention.',
    ],
    prevention: [
      'Most modern field corn hybrids carry dominant Rp genes providing high resistance.',
      'Plant early to avoid peak mid-season airborne spore migrations.',
    ],
  },
  {
    id: 'banana_black_leaf_streak',
    crop: 'Banana',
    disease: 'Black Sigatoka',
    pathogen: 'Pseudocercospora fijiensis',
    type: 'Fungal',
    severityRisk: 'Severe / Critical',
    symptoms: [
      'Tiny reddish-brown specks on underside of leaves developing into dark streak-like lesions.',
      'Streaks coalesce into black elliptical spots with sunken gray centers and yellow halos.',
      'Drastic reduction in functional photosynthetic leaf area leading to premature fruit ripening.',
    ],
    environmentalFactors: [
      'Tropical conditions: temperatures 26°C–28°C and high rainfall or continuous morning dew.',
      'Crowded plantations with poor drainage and stagnant air.',
    ],
    immediateActions: [
      'De-leafing: surgically cut out affected leaf portions and lay them face-down on plantation floor.',
      'Improve plantation ditch drainage to lower local canopy relative humidity.',
    ],
    prevention: [
      'Optimize planting density (e.g. 1,600 to 1,800 plants per hectare).',
      'Implement integrated resistance-management practices recommended by regional agronomic services.',
    ],
  },
  {
    id: 'grape_black_rot',
    crop: 'Grape',
    disease: 'Black Rot',
    pathogen: 'Phyllosticta ampelicida',
    type: 'Fungal',
    severityRisk: 'High',
    symptoms: [
      'Small, circular, reddish-brown spots with dark borders and black pycnidia on leaves.',
      'Infected berries shrivel into hard, black, wrinkled "mummies" that cling to the cluster.',
      'Shoots develop elongated, dark cankers that weaken canes.',
    ],
    environmentalFactors: [
      'Warm spring weather (24°C–29°C) with frequent showers.',
      'Leaves and berries requiring between 6 to 24 hours of continuous surface moisture.',
    ],
    immediateActions: [
      'Hand-remove and destroy all mummified grape clusters during dormant winter pruning.',
      'Consult local viticultural extension guides for protective canopy management options from bud break through bloom.',
    ],
    prevention: [
      'Canopy management (shoot thinning, leaf pulling around fruit zones) for rapid drying.',
      'Maintain clear herbicide strips or clean cultivation directly under the trellis wire.',
    ],
  },
  {
    id: 'grape_downy_mildew',
    crop: 'Grape',
    disease: 'Downy Mildew',
    pathogen: 'Plasmopara viticola',
    type: 'Oomycete',
    severityRisk: 'Severe',
    symptoms: [
      'Yellowish, oily translucent spots on upper leaf surfaces ("oil spots").',
      'Dense white downy growth on the underside of oil spots in high humidity.',
      'Infected young berries turn grayish-brown and drop or shrivel.',
    ],
    environmentalFactors: [
      'The "10-10-10" rule: 10 mm rainfall, temperatures ≥ 10°C, and shoot growth ≥ 10 cm.',
      'Warm, humid nights followed by morning dew.',
    ],
    immediateActions: [
      'Consider timely disease-management intervention based on local extension guidance and verified weather forecast risk.',
      'Prune sucker shoots close to the ground that act as spore ladders.',
    ],
    prevention: [
      'Orient vineyard rows parallel to prevailing winds for maximum canopy ventilation.',
      'Avoid overhead sprinkler frost protection when downy mildew risks are elevated.',
    ],
  },
  {
    id: 'wheat_leaf_rust',
    crop: 'Wheat',
    disease: 'Brown / Leaf Rust',
    pathogen: 'Puccinia triticina',
    type: 'Fungal',
    severityRisk: 'Moderate to High',
    symptoms: [
      'Small, round-to-oval orange-brown pustules scattered randomly over upper leaf blades.',
      'Pustules rub off on fingers as a bright orange-yellow powder.',
      'Premature death of the flag leaf leading to severe test weight reductions.',
    ],
    environmentalFactors: [
      'Temperatures between 15°C and 22°C with at least 6–8 hours of free dew on the leaf surface.',
      'Wind currents transporting urediniospores over hundreds of miles.',
    ],
    immediateActions: [
      'Scout flag leaves at boot through flowering stages (Feekes 10 to 10.5).',
      'Consider regionally approved disease-management options and consult local agricultural extension guidance before treatment.',
    ],
    prevention: [
      'Plant wheat varieties with multi-gene adult plant resistance (APR).',
      'Destroy "green bridge" volunteer wheat plants between cropping seasons.',
    ],
  },
  {
    id: 'cherry_leaf_spot',
    crop: 'Cherry',
    disease: 'Cherry Leaf Spot',
    pathogen: 'Blumeriella jaapii',
    type: 'Fungal',
    severityRisk: 'Moderate to High',
    symptoms: [
      'Tiny circular purple spots on the upper leaf surface that turn reddish-brown.',
      'Centers of lesions may drop out, creating a "shot-hole" appearance.',
      'Leaves turn bright yellow and drop prematurely, often defoliating trees by mid-summer.',
    ],
    environmentalFactors: [
      'Warm wet weather (16°C–20°C) with persistent leaf wetness.',
      'Inoculum overwintering in fallen leaves on the orchard floor.',
    ],
    immediateActions: [
      'Rake, shred, or disc fallen leaves into the soil to accelerate decomposition.',
      'Consult regional orchard management spray calendars and extension specialists for post-bloom foliar protection.',
    ],
    prevention: [
      'Ensure open canopy pruning to promote rapid evaporation of morning dew.',
      'Apply late-autumn orchard floor urea treatment to break down overwintering fungi.',
    ],
  },
  {
    id: 'bell_pepper_bacterial_spot',
    crop: 'Bell Pepper',
    disease: 'Bacterial Spot',
    pathogen: 'Xanthomonas campestris pv. vesicatoria',
    type: 'Bacterial',
    severityRisk: 'High',
    symptoms: [
      'Small, circular water-soaked lesions that turn brown with darker borders and yellow halos.',
      'Leaves become distorted, chlorotic, and drop heavily exposing fruit to sunscald.',
      'Fruit exhibits raised, rough, wart-like scab spots that crack and admit secondary rot.',
    ],
    environmentalFactors: [
      'Warm temperatures (24°C–30°C) combined with high rainfall, rain storms, and overhead irrigation.',
      'Wind-driven rain driving bacteria directly into natural leaf stomata and micro-wounds.',
    ],
    immediateActions: [
      'Avoid all cultivation or harvesting when plants are wet.',
      'Evaluate certified bacterial suppression strategies and consult agricultural extension specialists before applying treatments.',
    ],
    prevention: [
      'Plant only hot-water treated or certified disease-free pepper seeds.',
      'Use resistant pepper hybrids bred for multiple Xanthomonas races (Races 1–10).',
    ],
  },
];
